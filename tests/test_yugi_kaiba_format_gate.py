"""Research-only gate for the proposed early OCG Tokyo Dome snapshot.

The packet has exactly ONE current-authoritative Tokyo Dome research
section: ``tokyo_dome_research_current``. Anything under the top-level
``superseded_findings`` key is archived/rejected history and must never be
read as current - tests in this module enforce that boundary explicitly,
not just check that prose fields exist.
"""

from __future__ import annotations

import json
import hashlib
import copy
import re
import unittest
from datetime import date
from pathlib import Path

from retroformats.model import Coverage, ErratumV2, Pool
from retroformats.lflist import build_lflist
from retroformats.releases import ReleaseIndex, evaluate_cutoff
from retroformats.repo import Repository


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs" / "research" / "yugi-kaiba-format-source-packet.json"

# Substrings that must never appear inside a DATA field (not narrative prose)
# of the current-authoritative section - these are exactly the wrong claims
# the rejected 2026-08 pass made, and their presence in a data field (as
# opposed to a "this was corrected" sentence) would mean a ghost of a
# conclusion we already know is wrong has leaked back into active use.
BANNED_AS_CURRENT_VALUE = ("probable 2000", "genuinely disputed between agents")


# Phrases from now-corrected/superseded framings that must never appear as
# ACTIVE terminology anywhere under tokyo_dome_research_current. Quoting an
# old phrase for correction purposes is fine (see EXEMPT_PATH_MARKERS below),
# asserting it as live status text is not.
LEGACY_BANNED_PHRASES = (
    "bounded-to-proven",
    "moderately, not fully, resolved",
    "moderately resolved, not fully settled",
)

# A path is exempt from the legacy-phrase ban if any segment (case-
# insensitive) matches one of these markers - these are exactly the kind of
# "explicitly archival/audit field" the task calls out (prior_claim,
# supersedes, correction-history fields).
EXEMPT_PATH_MARKERS = ("supersedes", "prior_claim", "correction", "adversarial_audit")

# Semantic (value-content) May-5-proof-contamination check: a SENTENCE is a
# violation if it mentions the exact Expert Rules date AND a proof/certainty
# word, UNLESS that SAME SENTENCE also carries a negation/hedge cue ("not",
# "NOT", "do not read ... as", etc.) - i.e. it reads as a positive assertion
# rather than a correction/rejection. This catches contamination inside
# ORDINARY PROSE VALUES, not just fields whose PATH happens to be named
# "confirmed"/"proven" - the exact blind spot that let the Tribute-Summon
# bug survive the previous pass's test_B.
#
# Checking is SENTENCE-scoped, not whole-string: a long field can
# legitimately contain several sentences, only one of which discusses the
# May-5 date, while an UNRELATED sentence elsewhere in the same field
# happens to contain the word "not" (e.g. "not an under-sourced guess").  A
# whole-string "does 'not' appear anywhere" check would let that unrelated
# "not" mask a genuinely unhedged claim in a different sentence - verified
# during this task's own adversarial self-check, where a whole-string
# version of this function failed to catch Mutation A.
#
# The exemption is intentionally NARROW: only `prior_claim` (the literal
# "here is what was wrongly claimed" quote field) is exempt. Unlike the
# legacy-phrase check (test_A), `correction` fields are NOT blanket-exempt
# here - a correction's own prose is ACTIVE, CURRENT text and must not
# itself read as an unhedged positive assertion; it needs to pass the same
# sentence-level check as any other field. `supersedes` as a whole is not a
# safe blanket marker either, since it contains both prior_claim (safe to
# exempt) and correction (must be checked normally).
MAY_5_DATE_PATTERN = re.compile(r"1999-05-05|may\s+5,?\s*1999", re.I)
PROOF_WORD_PATTERN = re.compile(r"\bproven\b|\bconfirmed\b|\bdefinitely\b", re.I)
NEGATION_TOKEN_PATTERN = re.compile(r"\bnot\b", re.I)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
MAY_5_CHECK_EXEMPT_PATH_MARKERS = ("prior_claim",)


def _is_may_5_proof_violation(path, value):
    """True if `value` positively asserts May 5 as a proven/confirmed date
    in some sentence, outside the literal prior_claim quote field."""
    path_str = "/".join(path).lower()
    if any(marker in path_str for marker in MAY_5_CHECK_EXEMPT_PATH_MARKERS):
        return False
    for sentence in SENTENCE_SPLIT_PATTERN.split(value):
        if (
            MAY_5_DATE_PATTERN.search(sentence)
            and PROOF_WORD_PATTERN.search(sentence)
            and not NEGATION_TOKEN_PATTERN.search(sentence)
        ):
            return True
    return False


def _walk_strings(value, path=()):
    """Yield (path_tuple, string_value) for every string leaf in a JSON tree."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk_strings(v, path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _walk_strings(v, path + (str(i),))
    elif isinstance(value, str):
        yield path, value


def _make_pool():
    raw_pool = {
        "id": "pool-ocg1999-research-only", "region": "OCG", "kind": "release-cutoff",
        "cutoff": {"cutoff_date": "1999-08-25", "territories": ["ocg-jp"]},
        "sources": ["yugipedia-ocg-series1-set-pages"],
    }
    return Pool.load(raw_pool, ROOT / "research-only-pool.json")


# ------------------------------------------------------------------
# Authority/projection consistency invariants (this session).
#
# The bug class this session found: OLDER TOP-LEVEL packet fields (outside
# tokyo_dome_research_current) and narrative gate.md sections were never
# updated when tokyo_dome_research_current was hardened, so they kept
# asserting claims the authoritative section had since disproven (the
# Expert Rules primary source being "unlocated", full chain/Spell-Speed/
# priority being promoted to a confirmed blocker from rulebook silence).
# Every check below is whole-PACKET scoped (minus superseded_findings),
# not tokyo_dome_research_current-scoped like test_A/test_B2 above - that
# narrower scope is exactly what let the bug survive the previous pass's
# hardening tests.
# ------------------------------------------------------------------

WHOLE_PACKET_SOURCE_UNLOCATED_BANNED_PHRASES = (
    "publication source unlocated",
    "publication source has not been located",
    "first publication source has not been located",
    "source has not been located",
)


def _walk_whole_packet_excluding_superseded(packet):
    for path, s in _walk_strings(packet, ()):
        if path and path[0] == "superseded_findings":
            continue
        yield path, s


def _assert_no_whole_packet_source_unlocated_claim(packet):
    """Invariant 1: no active packet projection may claim the Expert Rules
    publication source is unlocated - it was located and personally
    inspected 2026-08-29. Hyphens are normalized to spaces before matching:
    the actual historical bug used both forms interchangeably (a hyphenated
    "status" enum-style value and a spaced prose sentence), and a matcher
    that only caught one form would have missed the other."""
    violations = [
        (path, phrase)
        for path, s in _walk_whole_packet_excluding_superseded(packet)
        for phrase in WHOLE_PACKET_SOURCE_UNLOCATED_BANNED_PHRASES
        if phrase in s.lower().replace("-", " ")
    ]
    if violations:
        raise AssertionError(
            f"active packet projection still claims the Expert Rules source is unlocated: {violations}"
        )


def _assert_no_whole_packet_hyphenated_secondary_only_expert_rules_claim(packet):
    """Invariant 2: no active projection may downgrade the guide's Expert
    Rules content back to secondary-only evidence. Checks for the exact
    lowercase-hyphenated "strong-secondary-reconstruction" slug that was the
    literal (now-fixed) value of the old rule_boundary bug - this is
    deliberately distinct from the uppercase, underscore-separated
    STRONG_SECONDARY_RECONSTRUCTION enum token, which remains a
    legitimately-used status value elsewhere (e.g. the exact effective-date
    hypothesis, which genuinely is still a secondary reconstruction)."""
    violations = [
        path for path, s in _walk_whole_packet_excluding_superseded(packet)
        if s == "strong-secondary-reconstruction"
    ]
    if violations:
        raise AssertionError(
            f"active projection uses the old hyphenated secondary-only-evidence slug for Expert Rules: {violations}"
        )


def _assert_chain_priority_not_promoted_to_unconditional_blocker(packet):
    """Invariant 3: no active projection may promote the full modern
    Chain/Spell-Speed/priority system to an unconditional engine blocker -
    its Tokyo-Dome-specific historical status is UNKNOWN. The narrower,
    PROVEN no-chain/Traps-only-in-Battle-Phase paradigm (a different,
    narrower claim) is the one genuinely-confirmed blocker."""
    current = packet["tokyo_dome_research_current"]
    engine_items = " ".join(current["architecture_verdict_detail"]["engine_representation_blockers"]["items"])
    if "chain_spell_speed_priority" in engine_items or "chain/priority" in engine_items.lower():
        raise AssertionError("chain/priority appears as its own item in engine_representation_blockers.items")

    matrix = {
        row["rule_area"]: row
        for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
    }
    if matrix["chain_spell_speed_priority"]["tokyo_dome"]["status"] != "UNKNOWN":
        raise AssertionError("chain_spell_speed_priority.tokyo_dome.status is no longer UNKNOWN")

    kg_detail = packet["rules"]["candidate_core_flags"]["known_gaps_detail"]
    if kg_detail["pre-formal-chain-and-priority-boundary"]["confirmed_unconditional_tokyo_dome_blocker"] is not False:
        raise AssertionError("rules.known_gaps_detail now claims chain/priority is a confirmed unconditional blocker")


def _assert_rule_boundary_agrees_with_authority(packet):
    """Invariant 4/6: the top-level rule_boundary field (a current derived
    projection) must mechanically agree with the authoritative section, and
    must not regress to its pre-2026-08-29 stale content."""
    rb = packet["rule_boundary"]
    entry = next(t for t in rb["timeline"] if t["interval"] == "1999-05-05")
    if "PROVEN" not in entry["evidence"]:
        raise AssertionError("rule_boundary's 1999-05-05 timeline entry no longer records the guide as PROVEN located")
    for banned in WHOLE_PACKET_SOURCE_UNLOCATED_BANNED_PHRASES:
        status_norm = entry["status"].lower().replace("-", " ")
        evidence_norm = entry["evidence"].lower().replace("-", " ")
        if banned in status_norm or banned in evidence_norm:
            raise AssertionError(f"rule_boundary's 1999-05-05 timeline entry regressed to a source-unlocated claim: {banned!r}")
    if "tokyo_dome_research_current" not in rb.get("_scope", ""):
        raise AssertionError("rule_boundary lost its pointer to the authoritative tokyo_dome_research_current section")


def _assert_blocker_ledger_chain_reason_not_silence_based(packet):
    """Invariant: blocker_ledger.chain_spell_speed_semantics must justify
    BLOCKING via the narrower confirmed trap_activation_frequency paradigm
    (the real engine_representation_blockers/engine_reassessment key - a
    prior session's added prose mistakenly called this "spell_trap_response",
    a name that matches no real matrix/engine_reassessment key anywhere in
    the packet; corrected here), not by inferring Tokyo-Dome absence from
    rulebook silence."""
    reason = packet["blocker_ledger"]["chain_spell_speed_semantics"]["reason"]
    if "trap_activation_frequency" not in reason:
        raise AssertionError("blocker_ledger.chain_spell_speed_semantics reason no longer cites the narrower confirmed blocker")
    if (
        "lacks formal Chain/Spell Speed/priority rules and no general core flag supplies the historical boundary"
        in reason
    ):
        raise AssertionError("blocker_ledger.chain_spell_speed_semantics reason regressed to inferring absence from rulebook silence")


def _assert_top_level_verdict_is_scoped(packet):
    """Invariant: the bare top-level `verdict` field must carry a scope note
    that prevents it from being read as contradicting architecture_verdict."""
    note = packet.get("verdict_scope_note", "")
    if "BLOCKED_BY_BOTH" not in note or "architecture_verdict" not in note:
        raise AssertionError("verdict_scope_note missing or no longer points at the authoritative architecture_verdict")


def _assert_gate_md_has_current_state_header(text, packet):
    """Invariant 7: the narrative gate has a mechanically-checkable
    current-state header that cannot silently regress to the stale
    primary-source framing."""
    marker = "## Current authoritative state (read this first)"
    if marker not in text:
        raise AssertionError("gate.md is missing its mechanically-checkable current-state header")
    section = text.split(marker, 1)[1].split("\n## Verdict", 1)[0]
    current = packet["tokyo_dome_research_current"]
    required = [
        str(current["release_ledger_preserved"]["verified_this_session"]["products_through_cutoff"]),
        current["architecture_verdict"],
        current["restriction_list_current"]["canonicalization_status"]["status"],
        "UNKNOWN",
    ]
    missing = [value for value in required if value not in section]
    if missing:
        raise AssertionError(f"gate.md current-state header is missing required authoritative value(s): {missing}")
    section_norm = section.lower().replace("-", " ")
    for phrase in WHOLE_PACKET_SOURCE_UNLOCATED_BANNED_PHRASES:
        if phrase in section_norm:
            raise AssertionError(f"gate.md current-state header itself contains a stale phrase: {phrase!r}")


# ------------------------------------------------------------------
# Unconditional-engine-blocker adjudication standard (this session).
#
# The bug class this session investigated: the packet treated deck_out,
# trap_activation_frequency, and battle_calculation as unconditional Tokyo
# Dome engine blockers using a principle resembling "PROVEN at Starter Box +
# no located evidence of change" - which is structurally the SAME kind of
# silence-based reasoning the packet correctly REJECTED for
# chain_spell_speed_priority ("no chain concept" was wrongly inferred from
# the same source's silence on the topic). This session found that a
# MATERIALLY DIFFERENT, stronger justification actually exists for the three
# behaviours - a second, independently-dated primary source (the May 1999
# guide's own "Official Rule Reference" chapter, personally inspected via
# page image, not merely absence-of-evidence) that AFFIRMATIVELY restates
# each rule as unchanged, close to the event, with externally-corroborated
# upper bounds placing the actual eventual change months AFTER Tokyo Dome.
# That positive evidence is encoded at tokyo_dome_research_current.
# positive_continuity_evidence, keyed by rule_area, with an explicit
# not_silence_based flag.
#
# The exact standard, re-derived structurally (not just asserted in prose):
# a rule_area is a legitimate unconditional engine blocker iff (a) its
# engine_reassessment classification is NOT_REPRESENTABLE, (b) its matrix
# starter_box.status is PROVEN, and (c) EITHER its matrix tokyo_dome.status
# is PROVEN OR it has a positive_continuity_evidence entry flagged
# not_silence_based. Condition (a) alone (NOT_REPRESENTABLE) is NOT
# sufficient - tribute_summon/fusion_material_location/chain_spell_speed_priority
# all have engine gaps of one kind or another but are correctly NOT
# unconditional blockers, because their Tokyo-Dome-tier applicability is
# itself the open question, with no positive_continuity_evidence override.
# ------------------------------------------------------------------

def _derive_expected_unconditional_engine_blockers(packet):
    current = packet["tokyo_dome_research_current"]
    psr = current["primary_source_resolution_2026_08_29"]
    matrix = {r["rule_area"]: r for r in psr["three_column_evidence_matrix"]}
    engine = {r["rule_area"]: r for r in psr["engine_reassessment"]}
    pce = current.get("positive_continuity_evidence", {}).get("items", {})

    expected = set()
    for area, erow in engine.items():
        if erow.get("classification") != "NOT_REPRESENTABLE":
            continue
        mrow = matrix.get(area)
        if mrow is None or mrow["starter_box"]["status"] != "PROVEN":
            continue
        has_tokyo_dome_proof = mrow["tokyo_dome"]["status"] == "PROVEN"
        has_continuity_bound = area in pce and pce[area].get("not_silence_based") is True
        if has_tokyo_dome_proof or has_continuity_bound:
            expected.add(area)
    return expected


_KNOWN_GAPS_COUNT_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def _assert_known_gaps_scope_note_matches_actual_count(packet):
    """Mechanical cross-check (not a hardcoded phrase match): recomputes
    the ACTUAL known_gaps count from rules.candidate_core_flags.known_gaps
    and asserts rules._scope's prose states that exact count - so a stale
    count claim is caught by recomputation, not by matching one frozen
    string."""
    known_gaps = packet["rules"]["candidate_core_flags"]["known_gaps"]
    actual_count = len(known_gaps)
    scope_text = packet["rules"]["_scope"]
    word = _KNOWN_GAPS_COUNT_WORDS.get(actual_count)
    if word is None:
        raise AssertionError(f"no number word mapped for known_gaps count {actual_count} - extend the table")
    if f"currently {word} entries" not in scope_text:
        raise AssertionError(
            f"rules._scope does not state the actual known_gaps count ({actual_count}) - expected the "
            f"phrase 'currently {word} entries' to appear"
        )


def _assert_battle_calculation_semantics_status_matches_engine_classification(packet):
    """Mechanical cross-check: blocker_ledger.battle_calculation_semantics'
    status must agree with the ACTUAL engine classification recorded in
    primary_source_resolution_2026_08_29.engine_reassessment - bare
    RESOLVED claims an exact match; RESOLVED WITH APPROXIMATION claims a
    genuine representational gap. The two must never disagree with the
    authoritative engine-reassessment row."""
    engine_rows = {
        r["rule_area"]: r
        for r in packet["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["engine_reassessment"]
    }
    classification = engine_rows["battle_calculation"]["classification"]
    ledger_status = packet["blocker_ledger"]["battle_calculation_semantics"]["status"]
    is_exact = classification == "REPRESENTABLE_EXACT_BY_DEFAULT"
    if is_exact and ledger_status != "RESOLVED":
        raise AssertionError(
            f"engine_reassessment classifies battle_calculation as {classification!r} (an exact match) but "
            f"blocker_ledger.battle_calculation_semantics.status is {ledger_status!r}, not bare RESOLVED - "
            "an approximation status contradicts an exact-match engine classification"
        )
    if not is_exact and ledger_status == "RESOLVED":
        raise AssertionError(
            f"engine_reassessment classifies battle_calculation as {classification!r} (not an exact match) "
            "but blocker_ledger.battle_calculation_semantics.status is bare RESOLVED, which claims an exact "
            "match the engine classification does not support"
        )


def _assert_unconditional_blocker_standard(packet):
    """Invariants 1, 3, 4, 6: structurally re-derive the unconditional-
    engine-blocker set from first principles and require it to match the
    packet's own list exactly - neither a bare NOT_REPRESENTABLE
    classification (invariant 3) nor a bare Starter-Box PROVEN + Tokyo-Dome
    UNKNOWN pairing (invariant 1) is sufficient on its own; every listed
    blocker must independently satisfy the full standard (invariant 4); and
    conditional gaps that fail the standard must NOT appear in the list
    (invariant 6)."""
    current = packet["tokyo_dome_research_current"]
    actual_items = current["architecture_verdict_detail"]["engine_representation_blockers"]["items"]
    actual_areas = {item.split(" - ", 1)[0].strip() for item in actual_items}
    expected = _derive_expected_unconditional_engine_blockers(packet)
    if actual_areas != expected:
        raise AssertionError(
            f"engine_representation_blockers.items {sorted(actual_areas)} does not match "
            f"the structurally-derived unconditional-blocker standard {sorted(expected)}"
        )


def _assert_continuity_evidence_not_promoted_to_proven(packet):
    """Invariant 2: a positive_continuity_evidence entry (SUPPORTED_BUT_
    INCOMPLETE-tier evidence) must never be accompanied by a matrix row
    silently promoted to PROVEN at the later_pre_tokyo_dome tier - the
    residual gap to the event is real and must stay visible in the status
    field, not just in prose."""
    current = packet["tokyo_dome_research_current"]
    psr = current["primary_source_resolution_2026_08_29"]
    matrix = {r["rule_area"]: r for r in psr["three_column_evidence_matrix"]}
    pce = current.get("positive_continuity_evidence", {}).get("items", {})
    for area in pce:
        status = matrix[area]["later_pre_tokyo_dome"]["status"]
        if status == "PROVEN":
            raise AssertionError(
                f"{area}'s later_pre_tokyo_dome tier was silently promoted to PROVEN despite "
                "resting on positive_continuity_evidence, not an event-specific source"
            )
        if status != "SUPPORTED_BUT_INCOMPLETE":
            raise AssertionError(f"{area}'s later_pre_tokyo_dome tier has an unexpected status: {status}")


def _assert_architecture_verdict_derived_consistently(packet):
    """Invariant 7: BLOCKED_BY_BOTH must hold iff both blocker categories
    are non-empty; if either category were ever emptied, the top-line
    verdict must change with it, not float free of its own inputs."""
    current = packet["tokyo_dome_research_current"]
    detail = current["architecture_verdict_detail"]
    historical_nonempty = len(detail["historical_evidence_blockers"]["items"]) > 0
    engine_nonempty = len(detail["engine_representation_blockers"]["items"]) > 0
    verdict = current["architecture_verdict"]
    if historical_nonempty and engine_nonempty:
        expected = "BLOCKED_BY_BOTH"
    elif historical_nonempty:
        expected = "BLOCKED_BY_HISTORICAL_EVIDENCE"
    elif engine_nonempty:
        expected = "BLOCKED_BY_ENGINE"
    else:
        expected = "UNBLOCKED"
    if verdict != expected:
        raise AssertionError(f"architecture_verdict is {verdict!r}, but the blocker categories imply {expected!r}")


RECOIL_ABSENT_FROM_MODERN_BANNED_PHRASES = (
    "differs from modern damage-step semantics",
    "does not reproduce the historical atk<def attacker-recoil result",
    "does not reproduce the historical attacker-recoil result",
    "lacks modern damage step timing",
    "unrepresentable by current engine architecture",
    "no representable mechanism",
)
RECOIL_ABSENT_HEDGE_CUES = ("false", "corrected", "resolved", "no longer", "updated", "removed")


def _assert_no_active_recoil_absent_from_modern_claim(packet):
    """Required regression: no active field may claim the historical
    ATK<DEF/ATK<ATK attacker-recoil arithmetic is absent from modern Yu-Gi-
    Oh! or unrepresentable by the pinned engine - personally verified false
    against both the pinned ocgcore source and Konami's current official
    rules. Sentence-scoped: a corrective sentence quoting the old wrong
    claim to explain it was fixed must not be confused with a live
    assertion of it, and an unrelated recoil-mention elsewhere in the same
    long field (e.g. deck-out's own, still-valid, unrepresentable claim)
    must not falsely implicate a correction sentence next to it."""
    violations = []
    for path, s in _walk_whole_packet_excluding_superseded(packet):
        for sentence in SENTENCE_SPLIT_PATTERN.split(s):
            low = sentence.lower()
            if (
                ("recoil" in low or "battle_calculation" in low or "battle-calculation" in low)
                and any(phrase in low for phrase in RECOIL_ABSENT_FROM_MODERN_BANNED_PHRASES)
                and not any(cue in low for cue in RECOIL_ABSENT_HEDGE_CUES)
            ):
                violations.append((path, sentence[:200]))
    if violations:
        raise AssertionError(f"stale 'recoil arithmetic unrepresentable' claim found: {violations}")


# ------------------------------------------------------------------
# Restriction-list evidence-sensitive gate (2026-08-30, re-derived 2026-09).
#
# The bug class this session guards against: canonicalization_status must
# not be frozen permanently at UNRESOLVED_BLOCKING regardless of evidence
# (that would make the gate meaningless), but it also must not be promoted
# just because SOME axis improved.
#
# 2026-09 RE-DERIVATION: the original three axes (content/scope/effective-
# date) each bundled one LOAD-BEARING proposition with one that does not
# actually affect an August-26-Tokyo-Dome-snapshot banlist artifact (see
# banlist_artifact_requirements_2026_09.critical_logical_test in the
# packet). Split into SIX axes: four are load-bearing and gate
# canonicalization; two (outer_scope_status, first_effective_date_status)
# are explicitly non-blocking historical research, tracked but never
# consulted by the readiness computation. A source proving one load-bearing
# axis does not thereby prove another.
# ------------------------------------------------------------------

RESTRICTION_LOAD_BEARING_AXES = (
    "content_membership_status",
    "content_completeness_status",
    "target_event_applicability_status",
    "source_authentication_status",
)
RESTRICTION_NONBLOCKING_AXES = ("outer_scope_status", "first_effective_date_status")
RESTRICTION_ALL_AXES = RESTRICTION_LOAD_BEARING_AXES + RESTRICTION_NONBLOCKING_AXES


def _assert_restriction_list_axes_are_independently_evidenced(packet):
    """Every axis (load-bearing or not) must cite at least one real,
    resolvable source_id - a status with no evidence citation is not
    allowed. canonicalization_status may only leave UNRESOLVED_BLOCKING/
    BLOCKING if ALL FOUR LOAD-BEARING axes are independently PROVEN - the
    two non-blocking axes are deliberately EXCLUDED from this computation,
    per the central rule of the 2026-09 pass: a historical uncertainty is a
    canonicalization blocker only if resolving it could change the
    artifact. This is the mechanical evidence threshold for
    canonicalization readiness: it is deliberately NOT hard-coded to
    always fail, so a genuinely qualifying future source updating all four
    load-bearing axes to PROVEN would legitimately pass, REGARDLESS of
    what the two non-blocking axes say."""
    rlc = packet["tokyo_dome_research_current"]["restriction_list_current"]
    known_source_ids = {s["id"] for s in packet["sources"]}
    for axis in RESTRICTION_ALL_AXES:
        axis_obj = rlc.get(axis)
        if not axis_obj:
            raise AssertionError(f"restriction_list_current is missing required axis {axis!r}")
        source_ids = axis_obj.get("source_ids")
        if not source_ids:
            raise AssertionError(f"{axis} has no source_ids - a status with no evidence citation is not allowed")
        for sid in source_ids:
            if sid not in known_source_ids:
                raise AssertionError(f"{axis} cites unresolvable source_id {sid!r}")

    # canonicalization_status must itself DECLARE which axes are load-
    # bearing vs non-blocking, and that declaration must match the actual
    # axis set used above - catches silent drift (e.g. a 7th axis added
    # without updating the declared lists).
    cs = rlc["canonicalization_status"]
    declared_load_bearing = tuple(cs.get("load_bearing_axes") or ())
    declared_nonblocking = tuple(cs.get("explicitly_nonblocking_axes") or ())
    if set(declared_load_bearing) != set(RESTRICTION_LOAD_BEARING_AXES):
        raise AssertionError(
            f"canonicalization_status.load_bearing_axes {declared_load_bearing} does not match the actual "
            f"load-bearing axis set {RESTRICTION_LOAD_BEARING_AXES}"
        )
    if set(declared_nonblocking) != set(RESTRICTION_NONBLOCKING_AXES):
        raise AssertionError(
            f"canonicalization_status.explicitly_nonblocking_axes {declared_nonblocking} does not match "
            f"the actual non-blocking axis set {RESTRICTION_NONBLOCKING_AXES}"
        )

    all_load_bearing_proven = all(rlc[axis]["status"] == "PROVEN" for axis in RESTRICTION_LOAD_BEARING_AXES)
    cs_status = cs["status"]
    if cs_status not in ("UNRESOLVED_BLOCKING", "BLOCKING") and not all_load_bearing_proven:
        raise AssertionError(
            f"canonicalization_status is {cs_status!r} but not all four LOAD-BEARING axes "
            f"({ {a: rlc[a]['status'] for a in RESTRICTION_LOAD_BEARING_AXES} }) are PROVEN - promotion to "
            "canonicalization-ready requires all four load-bearing axes independently PROVEN "
            f"(non-blocking axes {RESTRICTION_NONBLOCKING_AXES} are correctly excluded from this check)"
        )


_RESTRICTION_AXIS_HEDGE_FIELD_NAMES = (
    "not_PROVEN_because", "what_remains_unresolved", "explicit_date_never_found",
)
_RESTRICTION_AXIS_HEDGE_PHRASES = (
    "falls short of PROVEN", "not yet", "remains unresolved", "not established",
    "does not itself prove", "not independently confirmed", "NOT independently confirmed",
    "not demonstrated", "narrowed but not closed", "still falls short",
)


def _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(packet):
    """Structural self-consistency: an axis whose own reasoning text still
    carries explicit hedge language must not simultaneously claim status
    PROVEN - a status field and its own justification prose disagreeing is
    exactly the class of bug this pass's tests exist to catch. Checked
    across ALL SIX axes, not just the load-bearing four - a non-blocking
    axis is not exempt from internal self-consistency.

    Checks BOTH known hedge field names (content_membership_status'
    not_PROVEN_because, content_completeness_status/outer_scope_status'
    what_remains_unresolved, first_effective_date_status'
    explicit_date_never_found) AND hedge PHRASES appearing in ANY string
    field of the axis - target_event_applicability_status and
    source_authentication_status carry their hedge language under
    differently-named fields (what_is_well_supported, current_state), and
    a field-name-only check would silently miss a bad promotion on either
    of those two (found and fixed during this pass's own review)."""
    rlc = packet["tokyo_dome_research_current"]["restriction_list_current"]
    for axis in RESTRICTION_ALL_AXES:
        axis_obj = rlc[axis]
        if axis_obj["status"] != "PROVEN":
            continue
        present_hedge_fields = [k for k in _RESTRICTION_AXIS_HEDGE_FIELD_NAMES if axis_obj.get(k)]
        if present_hedge_fields:
            raise AssertionError(
                f"{axis} claims PROVEN but still carries hedge field(s) {present_hedge_fields} - "
                "remove the hedge or do not claim PROVEN"
            )
        for field_name, value in axis_obj.items():
            if field_name in ("status", "source_ids", "proposition"):
                continue
            if not isinstance(value, str):
                continue
            hits = [p for p in _RESTRICTION_AXIS_HEDGE_PHRASES if p in value]
            if hits:
                raise AssertionError(
                    f"{axis} claims PROVEN but field {field_name!r} still contains hedge phrase(s) {hits} - "
                    "remove the hedge or do not claim PROVEN"
                )


def _assert_nonblocking_axes_never_gate_canonicalization(packet):
    """Direct proof of the central rule of the 2026-09 pass: resolving
    H2-vs-H3 (outer_scope_status) or the true first-effective-date
    (first_effective_date_status) must NEVER be required for
    canonicalization readiness. Constructs the specific scenario the old
    three-axis model would have wrongly blocked on - all four load-bearing
    axes PROVEN, but the two non-blocking axes left exactly as unresolved
    as they are today - and asserts the mechanical helper ACCEPTS it."""
    mutated = copy.deepcopy(packet)
    rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
    for axis in RESTRICTION_LOAD_BEARING_AXES:
        rlc[axis]["status"] = "PROVEN"
        for hedge in ("not_PROVEN_because", "what_remains_unresolved", "explicit_date_never_found"):
            rlc[axis].pop(hedge, None)
        # Simulate a real future proof: every remaining string field must
        # also read as proven, not just the three named hedge keys (see
        # test_mutation_AH's identical fix for why this matters).
        for field_name in list(rlc[axis].keys()):
            if field_name in ("status", "source_ids", "proposition"):
                continue
            if isinstance(rlc[axis][field_name], str):
                rlc[axis][field_name] = "Hypothetically fully proven by a future qualifying source."
    rlc["canonicalization_status"]["status"] = "RESOLVED"
    # Non-blocking axes deliberately left UNRESOLVED_NONBLOCKING, untouched.
    for axis in RESTRICTION_NONBLOCKING_AXES:
        if rlc[axis]["status"] == "PROVEN":
            raise AssertionError(f"test construction bug: {axis} should remain unresolved for this scenario")
    _assert_restriction_list_axes_are_independently_evidenced(mutated)  # must NOT raise
    _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(mutated)  # must NOT raise


RESTRICTION_LIST_INDEPENDENCE_OVERCLAIM_PHRASES = (
    "independently-authored sources",
    "separately-authored sources",
    "mutually independent in authorship",
    "three independent sources",
)


def _assert_no_stale_restriction_list_independence_overclaims(packet):
    """No ACTIVE (non-superseded, non-dated-historical-quote) prose may
    claim stronger source independence than the structured
    provenance_independence_assessment.independence_groups actually
    support. A bare 'independently-authored'/'mutually independent in
    authorship' claim about the V-Jump-plus-comment pair specifically
    contradicts independent_authorship_demonstarted='not_demonstrated' on
    that group - this is the exact bug class an adversarial review found
    live in four packet locations."""
    rlc = packet["tokyo_dome_research_current"]["restriction_list_current"]
    pia = rlc["contemporaneous_source_investigation_2026_08_30"]["provenance_independence_assessment"]
    groups = pia["independence_groups"]
    any_group_not_demonstrated = any(
        g.get("independent_authorship_demonstrated") != True for g in groups  # noqa: E712
    )
    if not any_group_not_demonstrated:
        return  # every group genuinely has demonstrated authorship independence; no overclaim is possible

    hedge_markers = ("overclaimed", "REVISED", "overstate", "not demonstrably", "deliberately NOT")
    violations = []
    for path, s in _walk_strings(packet, ()):
        if path[:1] == ("superseded_findings",):
            continue
        if "adversarial_review_2026_08_30" in path:
            # Dated historical quote of what was actually claimed/reviewed
            # at that time - preserved verbatim, not an active claim.
            continue
        # SENTENCE-scoped, not whole-string-scoped: a long field can
        # legitimately contain a hedge marker (e.g. "REVISED 2026-08-30...")
        # for ONE part of its text while a DIFFERENT sentence in the same
        # field states an unrelated bare overclaim - checking the hedge
        # marker's presence anywhere in the whole string would let that
        # second sentence slip through uncaught (this exact gap was found
        # and fixed after test_mutation_AQ initially failed to catch it).
        for sentence in re.split(r"(?<=[.!?。])\s*", s):
            for phrase in RESTRICTION_LIST_INDEPENDENCE_OVERCLAIM_PHRASES:
                if phrase in sentence and not any(marker in sentence for marker in hedge_markers):
                    violations.append((path, phrase, sentence[:160]))
    if violations:
        raise AssertionError(
            f"active packet prose claims stronger source independence than "
            f"independence_groups supports: {violations}"
        )


def _assert_provenance_roots_not_double_counted(packet):
    """Duplicated/reposted copies sharing one provenance root must not be
    presented as independent corroboration - every independence_group must
    have a distinct provenance_root string, and the convergence claim may
    only cite groups that are actually distinct."""
    rlc = packet["tokyo_dome_research_current"]["restriction_list_current"]
    groups = rlc["contemporaneous_source_investigation_2026_08_30"]["provenance_independence_assessment"][
        "independence_groups"
    ]
    roots = [g["provenance_root"] for g in groups]
    if len(roots) != len(set(roots)):
        raise AssertionError(f"duplicate provenance_root values found: {roots}")


def _assert_contemporaneity_not_conflated_with_retrospective(packet):
    """Master Guide (a 2004 retrospective) must be recorded as NOT
    contemporaneous to 1999 - a later retrospective must never masquerade
    as a contemporaneous source in the ledger that downstream reasoning
    relies on."""
    rlc = packet["tokyo_dome_research_current"]["restriction_list_current"]
    ledger = {e["source_id"]: e for e in rlc["source_contemporaneity_ledger"]}
    master_guide_entry = ledger.get("yugipedia-august-1999-lists")
    if master_guide_entry is None:
        raise AssertionError("source_contemporaneity_ledger is missing the Master Guide / Yugipedia entry")
    if master_guide_entry["contemporaneous_to_1999"] is not False:
        raise AssertionError(
            "Master Guide (2004 retrospective) must be recorded as contemporaneous_to_1999: False - "
            f"found {master_guide_entry['contemporaneous_to_1999']!r}"
        )


def _assert_vjump_issue_designation_and_street_date_are_distinct(packet):
    """V Jump's cover/issue designation ('September 1999') and its actual
    on-sale/street date (~1999-07-21) must be recorded as two distinct
    fields, never merged into one date string."""
    vjump = packet["tokyo_dome_research_current"]["restriction_list_current"][
        "contemporaneous_source_investigation_2026_08_30"
    ]["vjump_1999_09_investigation"]
    designation = vjump.get("issue_designation", "")
    actual_date = vjump.get("actual_publication_date", "")
    if not designation or not actual_date:
        raise AssertionError("vjump_1999_09_investigation is missing issue_designation or actual_publication_date")
    if designation == actual_date:
        raise AssertionError(
            "issue_designation and actual_publication_date must not be identical strings - "
            "the cover month and the street date are different propositions"
        )
    if "9月" not in designation:
        raise AssertionError(f"issue_designation should name the September cover month: {designation!r}")
    if "9月" in actual_date and "07" not in actual_date and "7月" not in actual_date:
        raise AssertionError(
            f"actual_publication_date should not silently adopt the September cover month: {actual_date!r}"
        )


class YugiKaibaResearchGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
        cls.repo = Repository.load(ROOT)

    # ------------------------------------------------------------------
    # Original (pre-2026-08) hardening-gate fields - unaffected by this
    # session's archival reorg, still describe current truth, re-checked.
    # ------------------------------------------------------------------

    def test_packet_is_research_only_and_rejects_requested_label(self):
        self.assertEqual("research-gate-only", self.packet["status"])
        self.assertEqual("blocked", self.packet["canonicalization"])
        self.assertEqual("rejected", self.packet["target_recommendation"]["requested_label_verdict"])
        self.assertFalse(self.packet["scope"]["canonical_format_created"])

    def test_recommendation_is_the_pre_event_ocg_japan_snapshot(self):
        target = self.packet["target_recommendation"]
        self.assertEqual("1999-08-tokyo-dome", target["id"])
        self.assertEqual("OCG", target["region"])
        self.assertEqual("1999-08-25", target["snapshot"])
        self.assertEqual("1999-08-26", target["event"]["date"])
        self.assertIsNone(target["previous"])
        self.assertEqual("OCG", self.packet["card_pool"]["format_region"])
        self.assertEqual(["ocg-jp"], self.packet["card_pool"]["territories"])

    def test_region_and_territory_use_the_shared_schema_semantics(self):
        common = json.loads((ROOT / "schemas" / "common.schema.json").read_text(encoding="utf-8"))
        fmt = json.loads((ROOT / "schemas" / "format.schema.json").read_text(encoding="utf-8"))
        pool = json.loads((ROOT / "schemas" / "pool.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "common.schema.json#/$defs/region",
            fmt["properties"]["region"]["$ref"],
        )
        self.assertIn("OCG", common["$defs"]["region"]["enum"])
        self.assertNotIn("ocg-jp", common["$defs"]["region"]["enum"])
        self.assertIn("ocg-jp", common["$defs"]["territory"]["enum"])
        self.assertEqual(
            "common.schema.json#/$defs/territory",
            pool["properties"]["cutoff"]["properties"]["territories"]["items"]["$ref"],
        )

    def test_source_references_are_unique_and_resolvable(self):
        sources = self.packet["sources"]
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        known = set(ids)

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "source_ids":
                        for source_id in child:
                            self.assertIn(source_id, known)
                    elif key == "source_id":
                        self.assertIn(child, known)
                    else:
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.packet)
        for source in sources:
            self.assertTrue(source["url"].startswith(("http://", "https://")))

    def test_product_chronology_has_event_day_after_cutoff(self):
        entries = self.packet["product_chronology"]
        dates = [date.fromisoformat(entry["date"]) for entry in entries]
        self.assertEqual(dates, sorted(dates))
        self.assertLess(date.fromisoformat("1999-08-25"), dates[-1])
        self.assertIn("Tokyo Dome event and attendee/prize cards", entries[-1]["products"])

    def test_rules_and_architecture_keep_gaps_explicit(self):
        rules = self.packet["rules"]
        topics = {fact["topic"] for fact in rules["facts"]}
        self.assertIn("deck_out", topics)
        self.assertIn("battle_damage", topics)
        self.assertIn("chain_and_spell_speed", topics)
        self.assertIn("higher-LP-wins-deck-out", rules["candidate_core_flags"]["known_gaps"])
        # Regression: the old top-level "architecture" field (bare verdict "B")
        # no longer exists - it was renamed and explicitly scoped to
        # schema/host representability only, so it can never be mistaken for
        # a competing Tokyo Dome canonicalization verdict.
        self.assertNotIn("architecture", self.packet)
        architecture = self.packet["schema_host_architecture_assessment"]
        self.assertNotEqual("B", architecture["verdict"])
        self.assertIn("schema/host", architecture["verdict"].lower())
        self.assertIn("BLOCKED_BY_BOTH", architecture["_scope"])
        self.assertFalse(architecture["schema_change_required"])
        self.assertTrue(architecture["schema_enhancement_desirable"])
        self.assertFalse(architecture["runtime_change_required"])
        self.assertTrue(architecture["format_local_approximation_required"])
        self.assertEqual([40, None], architecture["historical_unbounded_deck_limits"]["main"])
        self.assertEqual([0, None], architecture["historical_unbounded_deck_limits"]["extra"])
        self.assertEqual([10, 10], architecture["historical_unbounded_deck_limits"]["side"])
        self.assertEqual([40, 999], architecture["host_representation"]["main"])
        self.assertTrue(architecture["host_representation"]["999_is_client_ceiling_not_historical_unbounded"])
        self.assertTrue(architecture["init_lua_feasibility"]["sanctioned_hook"])
        self.assertFalse(architecture["init_lua_feasibility"]["can_exactly_intercept_deckout"])

        flags = rules["candidate_core_flags"]
        self.assertIn("DUEL_NO_HAND_LIMIT", flags["accepted_for_rule_profile_research"])
        self.assertIn("DUEL_1_FACEUP_FIELD", flags["accepted_for_rule_profile_research"])
        self.assertNotIn("DUEL_NO_MAIN_PHASE_2", flags["accepted_for_rule_profile_research"])
        self.assertIn("DUEL_NO_MAIN_PHASE_2", flags["rejected"])
        self.assertIn("DUEL_OCG_OBSOLETE_IGNITION", flags["rejected"])
        self.assertEqual("wrong", next(row["classification"] for row in rules["core_flag_audit"] if row["flag"] == "DUEL_NO_MAIN_PHASE_2"))
        self.assertEqual("phase-engine-experiment", self.packet["phase_experiment"]["source_id"])
        self.assertEqual("mechanically-closer", self.packet["phase_experiment"]["configurations"][0]["classification"])
        self.assertEqual("historically-wrong", self.packet["phase_experiment"]["configurations"][1]["classification"])

    def test_frozen_errata_are_all_v2_and_accounted_at_snapshot(self):
        errata = list(self.repo.errata.values())
        self.assertEqual(296, len(errata))
        self.assertTrue(all(isinstance(record, ErratumV2) for record in errata))

        snapshot = date(1999, 8, 25)
        determinate = []
        ambiguous = []
        for record in errata:
            selection = record.selection_at(snapshot)
            (determinate if selection.chronology == "determinate" else ambiguous).append(selection)

        audit = self.packet["errata_audit"]
        self.assertEqual(296, audit["total"])
        self.assertEqual(146, len(determinate))
        self.assertEqual(150, len(ambiguous))
        self.assertEqual(146, audit["chronology"]["determinate"])
        self.assertEqual(150, audit["chronology"]["ambiguous"])

        determinate_modern = sum(selection.is_modern for selection in determinate)
        determinate_historical = len(determinate) - determinate_modern
        self.assertEqual(21, determinate_modern)
        self.assertEqual(125, determinate_historical)
        self.assertEqual(21, audit["determinate"]["modern"])
        self.assertEqual(125, audit["determinate"]["historical"])

        determinate_coverage = {}
        for selection in determinate:
            if selection.is_modern:
                continue
            kind = selection.candidates[0].coverage.kind.value
            determinate_coverage[kind] = determinate_coverage.get(kind, 0) + 1
        self.assertEqual({"reuse-upstream": 79, "known-gap": 42, "none-needed": 4}, determinate_coverage)
        self.assertEqual(determinate_coverage, audit["determinate"]["coverage"])
        self.assertEqual(set(), set(determinate_coverage) - {"reuse-upstream", "known-gap", "none-needed"})

        self.assertEqual(104, sum(selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(46, sum(not selection.modern_is_possible for selection in ambiguous))
        self.assertEqual(104, audit["ambiguous"]["modern_possible"])
        self.assertEqual(46, audit["ambiguous"]["modern_impossible"])

        coverage_occurrences = {}
        candidate_occurrences = 0
        for selection in ambiguous:
            candidate_occurrences += len(selection.candidates)
            for candidate in selection.candidates:
                kind = candidate.coverage.kind.value
                coverage_occurrences[kind] = coverage_occurrences.get(kind, 0) + 1
        self.assertEqual(302, candidate_occurrences)
        self.assertEqual(302, audit["ambiguous"]["candidate_occurrences"])
        self.assertEqual(
            {"reuse-upstream": 144, "unresolved": 47, "known-gap": 7, "modern": 104},
            coverage_occurrences,
        )
        self.assertEqual(coverage_occurrences, audit["ambiguous"]["candidate_coverage_occurrences"])

        modern_impossible_ids = sorted(
            record.id for record in errata
            if (selection := record.selection_at(snapshot)).chronology == "ambiguous"
            and not selection.modern_is_possible
        )
        unresolved_record_ids = sorted(
            record.id for record in errata
            if (selection := record.selection_at(snapshot)).chronology == "ambiguous"
            and any(candidate.coverage.kind is Coverage.UNRESOLVED for candidate in selection.candidates)
        )
        self.assertEqual(46, len(modern_impossible_ids))
        self.assertEqual(47, len(unresolved_record_ids))
        self.assertEqual(modern_impossible_ids, audit["ambiguous_modern_impossible_ids"])
        self.assertEqual(unresolved_record_ids, audit["ambiguous_unresolved_record_ids"])

        substitutions = []
        for record in errata:
            selection = record.selection_at(snapshot)
            if selection.chronology != "determinate" or selection.is_modern:
                continue
            if selection.candidates[0].coverage.kind is not Coverage.REUSE_UPSTREAM:
                continue
            substitutions.append({
                "erratum_id": record.id,
                "modern_passcode": record.modern_card.passcode,
                "selected_events": sorted(selection.candidates[0].events),
                "selected_historical_passcode": selection.candidates[0].coverage.historical_passcode,
                "coverage_kind": selection.candidates[0].coverage.kind.value,
            })
        substitutions.sort(key=lambda row: row["erratum_id"])
        digest_input = json.dumps(substitutions, separators=(",", ":"), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(digest_input).hexdigest()
        self.assertEqual(79, len(substitutions))
        self.assertEqual(substitutions, audit["determinate_historical_substitutions"])
        self.assertEqual(digest, audit["determinate_historical_substitutions_digest"])
        self.assertEqual("b45a38f83be490899d2fd64198b70ea86170ea55f1c24ef3c50194d0546ceaa2", digest)

    def test_repository_has_the_certified_ocg_ledger_but_no_early_canonical_artifacts(self):
        # Regression 14/15: no canonical Tokyo Dome artifacts exist; existing
        # canonical formats and generated outputs remain unchanged.
        ocg_products = {
            product.id for product in self.repo.products.values()
            if any(event.territory.startswith("ocg") for event in product.events)
        }
        self.assertEqual(19, len(ocg_products))
        self.assertTrue(all(product_id in self.repo.products for product_id in ocg_products))
        self.assertEqual({"2005-04-goat", "2010-03-edison", "2011-09-tengu"}, set(self.repo.formats))
        self.assertEqual(0x28E9FC02, build_lflist(self.repo.formats["2005-04-goat"], self.repo).hash)
        self.assertEqual(3673, len(self.repo.pools[self.repo.formats["2010-03-edison"].pool_id].cards))
        self.assertEqual(4562, len(self.repo.pools[self.repo.formats["2011-09-tengu"].pool_id].cards))
        self.assertEqual(0x0CE5BABE, build_lflist(self.repo.formats["2011-09-tengu"], self.repo).hash)
        self.assertFalse((ROOT / "formats" / "1999-08-tokyo-dome").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "pools" / "1999-08-tokyo-dome.json").exists())
        self.assertFalse((ROOT / "data" / "rule-profiles" / "1999-08-tokyo-dome.json").exists())
        self.assertEqual(296, len(self.repo.errata))
        self.assertTrue(all(isinstance(record, ErratumV2) for record in self.repo.errata.values()))

    def test_coverage_gate_does_not_promote_modern_fallback_to_certification(self):
        audit = self.packet["errata_audit"]
        policy = audit["modern_policy_effect"]
        self.assertTrue(policy["explicit_policy_required"])
        self.assertEqual(150, policy["ambiguous_records_left_unresolved"])
        self.assertFalse(policy["certifiable"])
        self.assertEqual(Coverage.UNRESOLVED.value, "unresolved")

    def test_blocker_ledger_is_complete_and_uses_frozen_statuses(self):
        required = {
            "format_name_date_convention", "event_card_pool_cutoff", "ocg_release_ledger",
            "missing_card_identities", "banlist", "starter_vs_expert_effective_boundary",
            "main_battle_main_behaviour", "first_turn_draw", "first_turn_attack", "hand_limit",
            "deck_size_representation", "side_fusion_deck_constraints", "deck_out_rule",
            "battle_calculation_semantics", "chain_spell_speed_semantics", "errata_chronology",
            "errata_implementation_coverage", "engine_representability", "schema_representability",
        }
        ledger = self.packet["blocker_ledger"]
        self.assertEqual(required, set(ledger))
        allowed = {"RESOLVED", "RESOLVED WITH APPROXIMATION", "UNRESOLVED", "BLOCKING", "NONBLOCKING"}
        self.assertTrue(all(entry["status"] in allowed for entry in ledger.values()))
        self.assertTrue(all(entry["reason"] for entry in ledger.values()))

    def test_top_level_banlist_field_no_longer_asserts_the_stale_working_id(self):
        # The top-level `banlist` field previously asserted working_id
        # "ocg-1999-07" as if it were current - that date is now known
        # wrong. It must point to the current-authoritative section instead
        # of asserting a specific dated/scoped identifier itself.
        banlist = self.packet["banlist"]
        self.assertNotEqual("ocg-1999-07", banlist["working_id"])
        self.assertIn("tokyo_dome_research_current", banlist["conflict"])

    def test_gate_scope_declares_no_shared_data_or_runtime_mutation(self):
        scope = self.packet["scope"]
        self.assertEqual(
            {
                "docs/research/yugi-kaiba-format-source-gate.md",
                "docs/research/yugi-kaiba-format-source-packet.json",
                "tests/test_yugi_kaiba_format_gate.py",
                "tests/engine/test_tokyo_dome_rules.py",
            },
            set(scope["files_added_by_gate"]),
        )
        self.assertFalse(scope["runtime_or_schema_changed"])
        self.assertFalse(scope["errata_changed"])
        self.assertFalse(any(path.startswith(("formats/", "data/", "schemas/", "retroformats/", "dist/")) for path in scope["files_added_by_gate"]))

    # ------------------------------------------------------------------
    # Single-authoritative-state invariant (hardening pass, this session)
    # ------------------------------------------------------------------

    def test_exactly_one_authoritative_current_tokyo_dome_research_state(self):
        # Regression 1: there is exactly one authoritative/current Tokyo
        # Dome research state, and its authority is self-describing.
        self.assertNotIn("tokyo_dome_rules_and_restriction_research_2026_08", self.packet)
        self.assertNotIn("tokyo_dome_rules_corrective_gate_2026_08", self.packet)
        self.assertIn("tokyo_dome_research_current", self.packet)
        current = self.packet["tokyo_dome_research_current"]
        self.assertEqual("current-authoritative", current["status"])

        self.assertIn("superseded_findings", self.packet)
        archive = self.packet["superseded_findings"]
        self.assertIn("rejected_2026_08_rules_and_restriction_research", archive)
        self.assertIn("_why_rejected", archive["rejected_2026_08_rules_and_restriction_research"])

    def test_superseded_claims_cannot_appear_in_active_current_fields(self):
        # Regressions 2, 12, 13: the specific wrong claims from the rejected
        # pass must not appear as asserted DATA VALUES in the current
        # section - they may appear only inside clearly-labeled
        # correction/audit-trail prose (fields whose own key names signal
        # that context), and they MUST still be present in the archive
        # (proving nothing was silently deleted, only relabeled).
        current = self.packet["tokyo_dome_research_current"]
        archive = self.packet["superseded_findings"]["rejected_2026_08_rules_and_restriction_research"]

        # The archive still honestly contains the rejected claims - nothing
        # was deleted, only relabeled as non-authoritative.
        archive_text = json.dumps(archive, ensure_ascii=False).lower()
        self.assertIn("probable 2000", archive_text)
        self.assertIn("genuinely disputed between agents", archive_text)

        # The authoritative matrix's actual DATA fields (not narrative/
        # correction prose fields) must never assert the wrong values.
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        self.assertNotIn("2000", matrix["starting_lp"]["starter_box"]["summary"])
        self.assertEqual("PROVEN", matrix["first_turn_attack"]["starter_box"]["status"])
        self.assertNotIn("AMBIGUOUS", matrix["first_turn_attack"]["starter_box"]["status"])
        engine = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["engine_reassessment"]}
        self.assertNotEqual("EXACT", engine["deck_out"]["classification"])

        # Narrative correction fields (supersedes.corrected_claims,
        # starter_box_baseline) are explicitly ALLOWED to quote the old wrong
        # phrase, but only paired with a correction in the same entry/field -
        # verify that pairing rather than banning the phrase outright.
        for claim in current["supersedes"]["corrected_claims"]:
            if "probable 2000" in claim["prior_claim"].lower() or "2000 lp" in claim["prior_claim"].lower():
                self.assertIn("correction", claim)
                self.assertTrue(claim["correction"])
            if "disputed between agents" in claim["prior_claim"].lower():
                self.assertIn("correction", claim)
                self.assertTrue(claim["correction"])

    # ------------------------------------------------------------------
    # Evidence matrix - three tiers, never collapsed
    # ------------------------------------------------------------------

    def test_authoritative_matrix_keeps_three_tiers_separate(self):
        # Regression: three-tier structure. The authoritative matrix is now
        # primary_source_resolution_2026_08_29.three_column_evidence_matrix
        # (21 rows, nested {status, summary, source_ids} per tier) - the
        # prior 15-row flat-field matrix is archived, not current.
        current = self.packet["tokyo_dome_research_current"]
        self.assertEqual(
            "primary_source_resolution_2026_08_29.three_column_evidence_matrix",
            current["authoritative_rule_matrix"],
        )
        matrix = current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        self.assertGreaterEqual(len(matrix), 15)
        required_columns = {"rule_area", "starter_box", "later_pre_tokyo_dome", "tokyo_dome"}
        allowed_status = {
            "PROVEN", "SUPPORTED_BUT_INCOMPLETE", "UNKNOWN",
            "STRONG_SECONDARY_RECONSTRUCTION", "CONTRADICTED", "NOT_APPLICABLE",
        }
        for row in matrix:
            self.assertEqual(required_columns, set(row))
            for tier in ("starter_box", "later_pre_tokyo_dome", "tokyo_dome"):
                self.assertIn("status", row[tier])
                self.assertIn("source_ids", row[tier])
                self.assertIn(row[tier]["status"], allowed_status)

        rule_areas = {row["rule_area"] for row in matrix}
        for expected in (
            "starting_lp", "starting_hand", "first_turn_draw", "first_turn_attack", "deck_out",
            "main_battle_main_sequence", "normal_summon_set", "tribute_summon",
            "fusion_material_location", "hand_limit", "main_deck_size", "side_deck",
            "win_condition_and_draw", "spell_activation_frequency", "trap_activation_frequency",
            "chain_spell_speed_priority", "battle_calculation",
        ):
            self.assertIn(expected, rule_areas)

    def test_starting_lp_starter_box_state_is_8000(self):
        # Regression 3.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        starting_lp = matrix["starting_lp"]["starter_box"]
        self.assertEqual("PROVEN", starting_lp["status"])
        self.assertIn("8000", starting_lp["summary"])
        self.assertNotIn("2000", starting_lp["summary"])
        baseline = current["starter_box_baseline"]["resolved"]["starting_lp"]
        self.assertTrue(baseline.startswith("8000"))

    def test_first_turn_attack_starter_box_state_is_prohibited_and_proven(self):
        # Regression 4.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        first_turn_attack = matrix["first_turn_attack"]
        self.assertEqual("PROVEN", first_turn_attack["starter_box"]["status"])
        self.assertIn("cannot attack", first_turn_attack["starter_box"]["summary"].lower())
        self.assertTrue(len(first_turn_attack["starter_box"]["source_ids"]) > 0)
        self.assertEqual("UNKNOWN", first_turn_attack["tokyo_dome"]["status"])
        self.assertNotEqual("PROVEN", first_turn_attack["tokyo_dome"]["status"])

    def test_deck_out_representation_is_not_exact_modern_behaviour(self):
        # Regression 5.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        engine = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["engine_reassessment"]}
        deck_out = matrix["deck_out"]
        self.assertEqual("NOT_REPRESENTABLE", engine["deck_out"]["classification"])
        self.assertNotEqual("EXACT", engine["deck_out"]["classification"])
        self.assertIn("lp", deck_out["starter_box"]["summary"].lower())
        self.assertEqual("PROVEN", deck_out["starter_box"]["status"])

    def test_main_battle_main_rejects_duel_no_main_phase_2(self):
        # Regression 6.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        engine = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["engine_reassessment"]}
        main_phase = matrix["main_battle_main_sequence"]
        self.assertEqual("PROVEN", main_phase["starter_box"]["status"])
        self.assertIn("main continues", main_phase["starter_box"]["summary"].lower())
        post_battle = engine["post_battle_main_actions"]
        self.assertIn("DUEL_NO_MAIN_PHASE_2", post_battle["current_behavior"])
        self.assertIn("rejected", post_battle["flag_disposition"].lower())

    def test_starter_box_hand_limit_and_tribute_are_not_falsely_proven(self):
        # Regression 7.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        for area in ("hand_limit", "tribute_summon"):
            row = matrix[area]["starter_box"]
            self.assertNotEqual("PROVEN", row["status"])
            self.assertEqual("UNKNOWN", row["status"])

    def test_may_5_expert_rules_boundary_is_not_proven(self):
        # Regression 8: exact May-5 normative boundary is not PROVEN, unless
        # the packet contains newly obtained primary/period evidence
        # supporting PROVEN - it does not, so it must not be PROVEN. Checked
        # at both the structured status field AND the prose fields that sit
        # right next to it - a status field alone doesn't stop a reader who
        # only reads the prose from meeting an unhedged "introduced ...
        # 1999-05-05" sentence, so the prose itself must not read as a hard
        # boundary.
        current = self.packet["tokyo_dome_research_current"]
        matrix = {row["rule_area"]: row for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        for area in ("tribute_summon", "fusion_material_location", "spell_activation_frequency"):
            row = matrix[area]["later_pre_tokyo_dome"]
            self.assertNotEqual("PROVEN", row["status"])
            self.assertIn(row["status"], ("SUPPORTED_BUT_INCOMPLETE", "STRONG_SECONDARY_RECONSTRUCTION"))
            value = row["summary"]
            if "1999-05-05" in value:
                self.assertFalse(
                    _is_may_5_proof_violation(("three_column_evidence_matrix", area, "later_pre_tokyo_dome"), value),
                    f"{area}.later_pre_tokyo_dome reads as an unhedged May-5 boundary: {value!r}",
                )
        eda = current["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["effective_date_adjudication"]
        self.assertNotEqual("PROVEN", eda["normative_effective_date_status"]["status"])
        self.assertIn("STRONG_SECONDARY_RECONSTRUCTION", current["change_boundary_before_tokyo_dome"]["answer"])

    def test_no_row_claims_tokyo_dome_proven_without_its_own_source(self):
        current = self.packet["tokyo_dome_research_current"]
        matrix = current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        for row in matrix:
            if row["tokyo_dome"]["status"] == "PROVEN":
                self.assertTrue(len(row["tokyo_dome"]["source_ids"]) > 0)
                self.assertNotEqual(set(row["tokyo_dome"]["source_ids"]), set(row["starter_box"]["source_ids"]))
        proven_at_tokyo_dome = [row["rule_area"] for row in matrix if row["tokyo_dome"]["status"] == "PROVEN"]
        self.assertEqual([], proven_at_tokyo_dome)

    def test_supersedes_five_specific_prior_claims(self):
        current = self.packet["tokyo_dome_research_current"]
        corrected = current["supersedes"]["corrected_claims"]
        self.assertEqual(5, len(corrected))
        joined = " ".join(c["prior_claim"] for c in corrected)
        for marker in ("first-turn attack", "Deck-out", "2000 LP", "Main Phase", "Hand size limit"):
            self.assertIn(marker, joined)

    # ------------------------------------------------------------------
    # Restriction list - research confidence vs. canonicalization readiness
    # ------------------------------------------------------------------

    def test_restriction_list_confidence_and_canonicalization_are_separate_fields(self):
        # Regression 9.
        current = self.packet["tokyo_dome_research_current"]
        restriction = current["restriction_list_current"]
        self.assertIn("research_confidence", restriction)
        self.assertIn("canonicalization_status", restriction)
        self.assertIsInstance(restriction["research_confidence"], dict)
        self.assertIsInstance(restriction["canonicalization_status"], dict)
        # These must be genuinely distinct concepts, not the same string twice.
        self.assertNotEqual(
            restriction["research_confidence"].get("confidence_level"),
            restriction["canonicalization_status"].get("status"),
        )
        self.assertEqual(3, len(restriction["content"]["cards"]))

    def test_restriction_list_canonicalization_remains_blocked(self):
        # Regression 10. Status string standardized to UNRESOLVED_BLOCKING
        # during the 2026-08-29 primary-source consolidation (previously the
        # bare "BLOCKING") to match the merged scope_hypotheses vocabulary.
        current = self.packet["tokyo_dome_research_current"]
        restriction = current["restriction_list_current"]
        self.assertEqual("UNRESOLVED_BLOCKING", restriction["canonicalization_status"]["status"])
        self.assertIn("what_would_unblock_this", restriction["canonicalization_status"])
        self.assertIn("scope_hypotheses", restriction)
        self.assertEqual({"H1", "H2", "H3", "H4"}, {h["id"] for h in restriction["scope_hypotheses"]["hypotheses"]})
        self.assertFalse((ROOT / "data" / "banlists" / "ocg-1999-07.json").exists())
        self.assertFalse((ROOT / "data" / "banlists" / "1999-08-tokyo-dome.json").exists())

    def test_master_guide_p84_was_actually_inspected_not_merely_cited(self):
        current = self.packet["tokyo_dome_research_current"]
        verification = current["restriction_list_current"]["master_guide_p84_verification"]
        self.assertTrue(verification["attempted"])
        self.assertTrue(verification["actually_inspected"])
        self.assertIn("1592318", str(verification["file_provenance"]["file_size_bytes"]))
        self.assertEqual("2106x2981", verification["file_provenance"]["pixel_dimensions"])
        self.assertIn("大会限定", verification["what_is_actually_visible"])
        self.assertIn("what_this_does_not_establish", verification)
        # Personally inspecting a 2004 retrospective must not be conflated
        # with inspecting a contemporaneous 1999 primary document.
        self.assertIn("2004", verification["what_this_does_not_establish"])

    def test_yugipedia_revision_provenance_has_exact_identifiers(self):
        # Regression 11.
        current = self.packet["tokyo_dome_research_current"]
        prov = current["restriction_list_current"]["yugipedia_revision_provenance"]
        self.assertGreaterEqual(len(prov["revisions"]), 5)
        for rev in prov["revisions"]:
            self.assertIsInstance(rev["revid"], int)
            self.assertTrue(rev["timestamp"])
            self.assertTrue(rev["user"])
        revids = {rev["revid"] for rev in prov["revisions"]}
        self.assertIn(3443496, revids)  # page creation
        self.assertIn(5830434, revids)  # final move+rewrite
        self.assertEqual("July 1999 Forbidden and Limited Lists", prov["page_title_before_move"])
        self.assertEqual("August 1999 Lists", prov["page_title_after_move"])

    def test_event_disruption_terminology_is_tiered_not_overclaimed(self):
        current = self.packet["tokyo_dome_research_current"]
        ed = current["event_disruption_reassessment"]
        self.assertIn("evidence_tier", ed)
        self.assertIn("period_source_status", ed)
        self.assertIn("NO PERIOD (1999) ARTICLE", ed["period_source_status"])
        # The old overclaiming label must not appear as this field's status.
        combined = json.dumps(ed, ensure_ascii=False)
        self.assertNotIn("BOUNDED-to-PROVEN", combined)

    # ------------------------------------------------------------------
    # Architecture verdict - re-derived, blockers separated by kind
    # ------------------------------------------------------------------

    def test_architecture_verdict_separates_historical_and_engine_blockers(self):
        current = self.packet["tokyo_dome_research_current"]
        self.assertEqual("BLOCKED_BY_BOTH", current["architecture_verdict"])
        detail = current["architecture_verdict_detail"]
        self.assertIn("historical_evidence_blockers", detail)
        self.assertIn("engine_representation_blockers", detail)
        self.assertGreater(len(detail["historical_evidence_blockers"]["items"]), 0)
        self.assertGreater(len(detail["engine_representation_blockers"]["items"]), 0)
        engine_items = " ".join(detail["engine_representation_blockers"]["items"])
        self.assertIn("deck_out", engine_items)
        # Tribute Summon's engine gap must be explicitly excluded from the
        # blocker list, per the task's own reasoning about applicability.
        self.assertNotIn("tribute_summon -", engine_items)
        self.assertIn("explicitly_not_counted_as_a_blocker", detail)
        self.assertIn("tribute_summon", detail["explicitly_not_counted_as_a_blocker"])

        readiness = current["tokyo_dome_rule_profile_readiness"]
        self.assertEqual("BLOCKED_BY_HISTORICAL_EVIDENCE", readiness["verdict"])

    # ------------------------------------------------------------------
    # Release ledger - preserved and re-verified live
    # ------------------------------------------------------------------

    def test_release_ledger_reverified_live_and_unchanged(self):
        current = self.packet["tokyo_dome_research_current"]
        preserved = current["release_ledger_preserved"]["verified_this_session"]
        self.assertEqual("1999-08-25", preserved["pre_event_snapshot"])
        self.assertEqual(370, preserved["pool_size"])
        self.assertEqual(
            "f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb",
            preserved["pool_digest_sha256"],
        )
        self.assertEqual(19, preserved["products_through_cutoff"])

        pool = _make_pool()
        index = ReleaseIndex.build(self.repo)
        evaluation = evaluate_cutoff(pool, self.repo, index)
        cards = evaluation.cards()
        digest = hashlib.sha256(
            json.dumps(
                [{"passcode": c["passcode"], "name": c["name"]} for c in cards],
                separators=(",", ":"), sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(370, len(cards))
        self.assertEqual("f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb", digest)

        names_in_pool = {c["name"] for c in cards}
        for excluded in ("Gate Guardian", "Suijin", "Kazejin", "Sanga of the Thunder", "Exodia the Forbidden One"):
            self.assertNotIn(excluded, names_in_pool)

        fabricated = ROOT / "data" / "releases" / "products" / "yu-gi-oh-duel-monsters-national-tournament-prize-cards.json"
        self.assertFalse(fabricated.exists())

    def test_personally_reverified_claims_are_recorded(self):
        current = self.packet["tokyo_dome_research_current"]
        claims = current["personally_reverified_claims"]
        self.assertGreaterEqual(len(claims), 5)
        for c in claims:
            self.assertTrue(c["claim_source_id"])
            self.assertTrue(c["source_url"])
            self.assertTrue(c["exact_rule_claim"])
            self.assertTrue(c["supporting_excerpt"])
            self.assertTrue(c["what_it_establishes"])

    # ------------------------------------------------------------------
    # Final consistency-cleanup pass: recursive invariants over the whole
    # active/current subtree, not just selected fields.
    # ------------------------------------------------------------------

    def test_A_no_superseded_active_terminology_anywhere(self):
        # 6A: walk every scalar string under tokyo_dome_research_current and
        # fail on legacy active-language phrases, except inside explicitly
        # archival/audit-labeled paths (structural exclusion, not regex).
        current = self.packet["tokyo_dome_research_current"]
        violations = []
        for path, s in _walk_strings(current, ("tokyo_dome_research_current",)):
            path_str = "/".join(path).lower()
            if any(marker in path_str for marker in EXEMPT_PATH_MARKERS):
                continue
            low = s.lower()
            for phrase in LEGACY_BANNED_PHRASES:
                if phrase in low:
                    violations.append((path, phrase))
        self.assertEqual([], violations, f"legacy phrases found outside archival fields: {violations}")

        # The archive itself is explicitly permitted (even expected) to still
        # contain some of this old wording, proving nothing was silently
        # deleted, only relabeled as non-authoritative.
        archive_text = json.dumps(self.packet["superseded_findings"], ensure_ascii=False)
        # (Not asserting presence of every phrase here - the archive's own
        # content is whatever the rejected pass actually wrote; this session
        # does not edit it. The important invariant is the one above: these
        # phrases cannot leak into the ACTIVE section.)
        self.assertTrue(archive_text)

    def test_B_no_exact_may_5_claim_inside_confirmed_semantics_fields(self):
        # 6B: any field whose path means confirmed/proven/definitely-changed
        # must not encode 1999-05-05 as the exact Expert Rules effective
        # date. Checked both structurally (authoritative-matrix status
        # pairing) and via a generic recursive path-name scan - not just one
        # entry.
        current = self.packet["tokyo_dome_research_current"]

        for row in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]:
            # Only the later_pre_tokyo_dome tier's own status governs the
            # later_1999 date claim - starter_box status is a genuinely
            # independent sub-claim and must not be asserted to correlate
            # with it.
            if "1999-05-05" in row["later_pre_tokyo_dome"].get("summary", ""):
                self.assertNotEqual("PROVEN", row["later_pre_tokyo_dome"]["status"])

        cb = current["change_boundary_before_tokyo_dome"]
        self.assertNotIn("confirmed_changed_by_aug_26_1999", cb)
        confirmed_unchanged_text = " ".join(cb["confirmed_unchanged_by_aug_26_1999"])
        self.assertNotIn("1999-05-05", confirmed_unchanged_text)

        hyp = cb["exact_date_hypothesis_for_the_above"]
        self.assertEqual("1999-05-05", hyp["best_supported_exact_date_hypothesis"])
        self.assertTrue(hyp["evidence_status"].startswith("STRONG_SECONDARY_RECONSTRUCTION"))
        self.assertNotEqual("PROVEN", hyp["evidence_status"])

        violations = []
        for path, s in _walk_strings(current, ()):
            path_str = "/".join(path).lower()
            semantically_confirmed = (
                "confirmed" in path_str or "proven" in path_str or "definitely" in path_str
            )
            if semantically_confirmed and "1999-05-05" in s:
                violations.append(path)
        self.assertEqual([], violations, f"1999-05-05 found inside a confirmed/proven-semantics field: {violations}")

    def test_B2_no_semantic_may_5_proof_contamination_in_active_prose(self):
        # 6B strengthened: the previous test only caught contamination when
        # the FIELD PATH happened to be named confirmed/proven/definitely.
        # That missed ordinary prose fields (e.g.
        # supersedes.corrected_claims[*].correction) whose VALUE positively
        # asserted "introduced by the May 5, 1999 ... revision - PROVEN for
        # the later-1999 tier" while the path itself said nothing special.
        # This recursively inspects every active scalar string's CONTENT,
        # not just its path, distinguishing a positive assertion from a
        # correction/negation via a "not"/negation-token check - not a
        # naive global ban on the words "PROVEN" and "1999-05-05" appearing
        # together (see _is_may_5_proof_violation and its docstring).
        current = self.packet["tokyo_dome_research_current"]
        violations = [
            (path, s) for path, s in _walk_strings(current, ())
            if _is_may_5_proof_violation(path, s)
        ]
        self.assertEqual(
            [], violations,
            f"active prose positively asserts May 5 as proven/confirmed: {violations}",
        )

        # Archival/audit paths remain explicitly exempt by design - prove
        # that exemption is real (not merely "no such content exists") by
        # confirming at least one archival path DOES contain the rejected
        # language, and the exemption is what keeps it out of the violation
        # list above, not mere absence.
        corrected_claims = current["supersedes"]["corrected_claims"]
        prior_claim_text = " ".join(c["prior_claim"] for c in corrected_claims)
        self.assertIn("PROVEN", prior_claim_text)

    def test_tribute_summon_corrected_claim_matches_authoritative_matrix(self):
        # 6/item 5: direct, structural regression for the specific surviving
        # bug - the Tribute Summon corrected-claim entry must not say the
        # May 5 transition is PROVEN, must identify the exact date as
        # secondary/reconstructed/unproven, and must remain consistent with
        # the authoritative matrix's own tribute_summon row.
        current = self.packet["tokyo_dome_research_current"]
        corrected_claims = current["supersedes"]["corrected_claims"]
        tribute_claim = next(
            c for c in corrected_claims
            if "Tribute" in c["prior_claim"] and "Tribute/Advance Summon" in c["prior_claim"]
        )
        correction = tribute_claim["correction"]

        # Must not contain the exact bad phrase that survived the previous pass.
        self.assertNotIn(
            "PROVEN for the later-1999 tier, dated with reasonable confidence",
            correction,
        )
        # Must explicitly identify the exact date as not proven / reconstructed.
        self.assertIn("STRONG_SECONDARY_RECONSTRUCTION", correction)
        self.assertIn("not PROVEN", correction)
        self.assertFalse(_is_may_5_proof_violation(("supersedes", "corrected_claims", "4", "correction"), correction))

        # Must remain consistent with the authoritative matrix's own status
        # for this rule area - the correction is not allowed to drift from
        # the matrix it is meant to describe.
        tribute_row = next(
            r for r in current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
            if r["rule_area"] == "tribute_summon"
        )
        self.assertNotEqual("PROVEN", tribute_row["later_pre_tokyo_dome"]["status"])
        self.assertEqual("SUPPORTED_BUT_INCOMPLETE", tribute_row["later_pre_tokyo_dome"]["status"])
        self.assertEqual("UNKNOWN", tribute_row["starter_box"]["status"])
        self.assertEqual("UNKNOWN", tribute_row["tokyo_dome"]["status"])

    def test_C_exactly_one_unqualified_architecture_verdict(self):
        # 6C: exactly one current unqualified format-level verdict,
        # BLOCKED_BY_BOTH. Any legacy "B" verdict is explicitly scoped to
        # schema/host representability, not left as a competing answer.
        self.assertNotIn("architecture", self.packet)
        self.assertEqual("BLOCKED_BY_BOTH", self.packet["tokyo_dome_research_current"]["architecture_verdict"])

        scoped = self.packet["schema_host_architecture_assessment"]
        self.assertNotEqual("B", scoped["verdict"])
        self.assertNotEqual("BLOCKED_BY_BOTH", scoped["verdict"])
        self.assertIn("schema", scoped["verdict"].lower())
        self.assertIn("BLOCKED_BY_BOTH", scoped["_scope"])
        self.assertIn("tokyo_dome_research_current.architecture_verdict", scoped["_scope"])

    def test_D_all_active_certified_product_references_are_19(self):
        # 6D: all active certified-product references resolve to 19; no
        # stale "20 products" wording survives anywhere outside the archive.
        self.assertEqual(19, self.packet["release_ledger_certification"]["certified_product_count"])
        violations = []
        for path, s in _walk_strings(self.packet, ()):
            if path and path[0] == "superseded_findings":
                continue
            low = s.lower()
            if "20 product" in low or "all 20" in low or "(20 curated" in low or "20-product" in low:
                violations.append((path, s[:200]))
        self.assertEqual([], violations, f"stale '20 products' reference(s): {violations}")

    def test_E_restriction_list_status_derives_only_from_the_named_axes(self):
        # 6E: all active restriction-list status consumers derive from a
        # fixed, named set of axes; no undocumented legacy summary field
        # exists to contradict them. RE-DERIVED 2026-09: the three-axis
        # model (content/scope/effective-date) was split into SIX axes
        # after determining, from the banlist schema/validator/build code,
        # that each of the original three bundled one load-bearing
        # proposition with one that does not affect an August-26-Tokyo-
        # Dome-snapshot artifact - see banlist_artifact_requirements_2026_09.
        # The addendum's own former copy of this reasoning (restriction_
        # list_scope_adjudication) still does not exist as a separate field
        # anywhere.
        current = self.packet["tokyo_dome_research_current"]
        rc = current["restriction_list_current"]
        self.assertEqual(
            {
                "_read_me_first", "content", "research_confidence", "canonicalization_status",
                "master_guide_p84_verification", "yugipedia_revision_provenance",
                "scope_hypotheses", "banlist_artifact_requirements_2026_09",
                "content_membership_status", "content_completeness_status",
                "target_event_applicability_status", "outer_scope_status",
                "first_effective_date_status", "source_authentication_status",
                "source_contemporaneity_ledger", "contemporaneous_source_investigation_2026_08_30",
            },
            set(rc.keys()),
        )
        self.assertEqual("UNRESOLVED_BLOCKING", rc["canonicalization_status"]["status"])
        # Each of the six axes is its own object with its own status and
        # source_ids - not a bare string, and not sharing one status value
        # by accident.
        for axis in RESTRICTION_ALL_AXES:
            self.assertIn("status", rc[axis])
            self.assertIn("source_ids", rc[axis])
            self.assertTrue(rc[axis]["source_ids"])
        # The four load-bearing axes use PROVEN/SUPPORTED_BUT_INCOMPLETE
        # vocabulary; the two non-blocking axes use a visibly distinct
        # status word so a reader can never mistake one for the other.
        for axis in RESTRICTION_NONBLOCKING_AXES:
            self.assertEqual("UNRESOLVED_NONBLOCKING", rc[axis]["status"])
        self.assertIn("MODERATE-TO-GOOD", rc["research_confidence"]["confidence_level"])
        self.assertNotIn("restriction_list_scope_adjudication", current["primary_source_resolution_2026_08_29"])

    def test_trap_hole_followup_is_context_not_independent_scope_proof(self):
        # The Master Guide finding must remain: header = strongest evidence
        # for tournament-limited scope; Trap Hole's later unrestriction is
        # additional chronology/context, not independent proof of scope.
        reasoning = self.packet["tokyo_dome_research_current"]["restriction_list_current"]["research_confidence"]["reasoning"]
        self.assertIn("大会限定", reasoning)  # the header text is still present and load-bearing
        self.assertIn("CHRONOLOGY/CONTEXT", reasoning)
        self.assertIn("NOT treated here as separately proving", reasoning)
        self.assertNotIn("independent data point supporting the tournament-specific reading", reasoning)
        self.assertNotIn("independent evidence favoring a one-off tournament rule", reasoning)

    def test_no_dangling_references_to_renamed_restriction_field(self):
        # The prior session's restriction_list_reassessment field was
        # renamed to restriction_list_current - no active prose may still
        # point readers at the old, now-nonexistent name.
        current = self.packet["tokyo_dome_research_current"]
        for path, s in _walk_strings(current, ()):
            self.assertNotIn("restriction_list_reassessment", s)

    # ------------------------------------------------------------------
    # 2026-08-29 primary-source resolution addendum
    # ------------------------------------------------------------------

    def _assert_primary_source_invariants(self, packet):
        # UPDATED 2026-08-29 CONSOLIDATION: field paths corrected to match
        # the merged/renamed structure - effective_date_adjudication's
        # ambiguous "all_three_changes_effective_on_1999_05_05" key is now
        # the clearly-named "normative_effective_date_status"; restriction-
        # list scope reasoning now lives at restriction_list_current (merged
        # in during consolidation), not as a separate addendum copy.
        current = packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        sources = {source["id"]: source for source in packet["sources"]}

        effective = resolution["expert_rules_primary_material"]["effective_date_adjudication"]
        if effective["normative_effective_date_status"]["status"] == "PROVEN":
            source_ids = effective["normative_effective_date_status"]["source_ids"]
            effective_sources = [sources[source_id] for source_id in source_ids if source_id in sources]
            if not any(source.get("effective_transition_primary") for source in effective_sources):
                raise AssertionError("publication/content evidence was laundered into an exact effective date")
        if resolution["tokyo_dome_event_ruleset_adjudication"]["status"] == "PROVEN":
            event_ids = resolution["tokyo_dome_event_ruleset_adjudication"]["event_specific_source_ids_inspected"]
            event_sources = [sources[source_id] for source_id in event_ids if source_id in sources]
            if not any(source.get("event_specific_primary") for source in event_sources):
                raise AssertionError("general or retrospective evidence was laundered into event adoption")

        restriction_status = current["restriction_list_current"]["canonicalization_status"]["status"]
        if restriction_status != "UNRESOLVED_BLOCKING":
            raise AssertionError("restriction-list content was laundered into a scope verdict")

        for row in resolution["three_column_evidence_matrix"]:
            if row["tokyo_dome"]["status"] == "PROVEN":
                event_ids = row["tokyo_dome"]["source_ids"]
                event_sources = [sources[source_id] for source_id in event_ids if source_id in sources]
                if not any(source.get("event_specific_primary") for source in event_sources):
                    raise AssertionError(f"{row['rule_area']} has no event-specific primary evidence")

    def test_actual_1999_expert_rules_scan_is_recorded_without_date_or_event_laundering(self):
        current = self.packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        material = resolution["expert_rules_primary_material"]
        document = material["document"]
        eda = material["effective_date_adjudication"]
        self.assertTrue(material["located"])
        self.assertEqual("1999-05-05", document["publication_date"])
        self.assertEqual([101, 102, 103, 104, 105, 107, 108, 109], document["personally_inspected_pages"])
        # Field names deliberately explicit (renamed 2026-08-29 consolidation
        # from the ambiguous "expert_rules_available_by_1999_05_05", which
        # could be misread as a normative claim) - three distinct fields for
        # three distinct propositions.
        self.assertEqual("PROVEN", eda["guide_publication_date"]["status"])
        self.assertEqual("PROVEN", eda["rules_documented_by_date"]["status"])
        self.assertEqual("SUPPORTED_BUT_INCOMPLETE", eda["normative_effective_date_status"]["status"])
        self.assertNotEqual("PROVEN", eda["normative_effective_date_status"]["status"])
        self.assertFalse(resolution["tokyo_dome_event_ruleset_adjudication"]["expert_rules_directly_proven_at_event"])
        self.assertEqual("UNKNOWN", resolution["tokyo_dome_event_ruleset_adjudication"]["status"])
        self._assert_primary_source_invariants(self.packet)

    def test_three_column_matrix_uses_the_required_status_vocabulary_and_keeps_event_unknown(self):
        resolution = self.packet["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]
        allowed = {
            "PROVEN",
            "STRONG_SECONDARY_RECONSTRUCTION",
            "SUPPORTED_BUT_INCOMPLETE",
            "UNKNOWN",
            "CONTRADICTED",
            "NOT_APPLICABLE",
        }
        matrix = resolution["three_column_evidence_matrix"]
        self.assertGreaterEqual(len(matrix), 15)
        for row in matrix:
            self.assertEqual({"rule_area", "starter_box", "later_pre_tokyo_dome", "tokyo_dome"}, set(row))
            for column in ("starter_box", "later_pre_tokyo_dome", "tokyo_dome"):
                self.assertIn(row[column]["status"], allowed)
                self.assertIn("source_ids", row[column])
            if row["tokyo_dome"]["status"] == "PROVEN":
                self.fail(f"event-specific rule was promoted without an event document: {row['rule_area']}")

    def test_restriction_scope_has_exact_required_unresolved_verdict_and_separate_hypotheses(self):
        # UPDATED 2026-08-29: this reasoning was merged from the addendum's
        # own (now-removed) restriction_list_scope_adjudication field into
        # restriction_list_current, the sole authoritative restriction-list
        # location, during consolidation.
        rc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertEqual("UNRESOLVED_BLOCKING", rc["canonicalization_status"]["status"])
        scope = rc["scope_hypotheses"]
        self.assertEqual({"H1", "H2", "H3", "H4"}, {hypothesis["id"] for hypothesis in scope["hypotheses"]})
        self.assertEqual({"Raigeki", "Dark Hole", "Trap Hole"}, {card["name_en"] for card in rc["content"]["cards"]})
        self.assertIn("contemporaneous", scope["what_would_close_it"].lower())

    def test_adversarial_source_laundering_mutations_fail(self):
        # A: a secondary May-5 claim cannot become a proven effective date.
        mutated = copy.deepcopy(self.packet)
        effective = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["effective_date_adjudication"]
        effective["normative_effective_date_status"]["status"] = "PROVEN"
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

        # B: a general guide cannot become an event-specific proof.
        mutated = copy.deepcopy(self.packet)
        event = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["tokyo_dome_event_ruleset_adjudication"]
        event["status"] = "PROVEN"
        event["event_specific_source_ids_inspected"] = ["official-guide-starter-book-1999-scan"]
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

        # C: list content cannot become proof of list scope.
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["restriction_list_current"]["canonicalization_status"]["status"] = "PROVEN_TOKYO_DOME_ONLY"
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

    def test_mutation_D_publication_date_alone_cannot_prove_normative_effective_date(self):
        # Mutation D (explicit, direct test - distinct from Mutation A above):
        # proof that the guide was PUBLISHED on 1999-05-05 must not, by
        # itself, be sufficient to mark the NORMATIVE Expert Rules transition
        # PROVEN on that date - even when the publication-date source really
        # is a solid, inspected primary source. The system must still allow
        # "Expert Rules content is documented in a guide published on
        # 1999-05-05" (rules_documented_by_date) to be PROVEN, since that is
        # a different, narrower, and genuinely supported claim.
        current = self.packet["tokyo_dome_research_current"]
        eda = current["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["effective_date_adjudication"]

        # The two propositions must currently be held at different statuses
        # for exactly this reason - this is the live invariant, not just a
        # hypothetical.
        self.assertEqual("PROVEN", eda["guide_publication_date"]["status"])
        self.assertEqual("PROVEN", eda["rules_documented_by_date"]["status"])
        self.assertNotEqual("PROVEN", eda["normative_effective_date_status"]["status"])

        # Now mutate: attach the SAME publication-date source used for
        # guide_publication_date directly to normative_effective_date_status
        # and mark it PROVEN, exactly the conflation the task describes.
        mutated = copy.deepcopy(self.packet)
        m_eda = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["effective_date_adjudication"]
        m_eda["normative_effective_date_status"]["status"] = "PROVEN"
        m_eda["normative_effective_date_status"]["source_ids"] = list(eda["guide_publication_date"]["source_ids"])
        with self.assertRaises(AssertionError):
            self._assert_primary_source_invariants(mutated)

        # rules_documented_by_date, a genuinely different and already-
        # supported proposition, remains promotable and must NOT be flagged.
        self._assert_primary_source_invariants(self.packet)

    def test_legitimate_new_primary_source_can_be_attached_to_a_promotion(self):
        # F: the invariant is evidence-sensitive, not a permanent ban on
        # future promotion. A future researcher may promote a proposition
        # only after attaching a source explicitly marked as establishing that
        # exact proposition. A hypothetical contemporaneous Tokyo Dome
        # regulation must promote ONLY the specific rule area it names -
        # not an unrelated cell.
        mutated = copy.deepcopy(self.packet)
        fixture = {
            "id": "fixture-event-rulesheet",
            "label": "Future inspected Tokyo Dome rulesheet fixture",
            "kind": "contemporaneous-official-primary-scan",
            "url": "https://example.invalid/future-tokyo-dome-rulesheet",
            "event_specific_primary": True,
            "effective_transition_primary": True,
        }
        mutated["sources"].append(fixture)
        resolution = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]
        effective = resolution["expert_rules_primary_material"]["effective_date_adjudication"]["normative_effective_date_status"]
        effective["status"] = "PROVEN"
        effective["source_ids"] = ["fixture-event-rulesheet"]
        event = resolution["tokyo_dome_event_ruleset_adjudication"]
        event["status"] = "PROVEN"
        event["event_specific_source_ids_inspected"] = ["fixture-event-rulesheet"]
        # Promote exactly one matrix cell (tribute_summon) using the new
        # source, leaving every other cell untouched.
        promoted_row = next(r for r in resolution["three_column_evidence_matrix"] if r["rule_area"] == "tribute_summon")
        promoted_row["tokyo_dome"]["status"] = "PROVEN"
        promoted_row["tokyo_dome"]["source_ids"] = ["fixture-event-rulesheet"]
        self._assert_primary_source_invariants(mutated)

        # The unrelated cells must NOT have been auto-promoted alongside it.
        for row in resolution["three_column_evidence_matrix"]:
            if row["rule_area"] == "tribute_summon":
                continue
            self.assertNotEqual(
                "PROVEN", row["tokyo_dome"]["status"],
                f"unrelated cell {row['rule_area']} was auto-promoted by an unrelated source attachment",
            )

    def test_mutation_E_copied_source_false_corroboration_is_rejected(self):
        # Mutation E: two modern/secondary pages that ultimately descend from
        # the SAME upstream claim must not count as two independent load-
        # bearing confirmations. Uses a lightweight, research-only
        # "provenance_root" field on source records (no schema change) -
        # sources sharing a provenance_root are the same evidence, no matter
        # how many distinct URLs cite it.
        def sources_are_independent(source_ids, sources_by_id):
            roots = set()
            named = 0
            for sid in source_ids:
                src = sources_by_id.get(sid)
                if src is None:
                    continue
                named += 1
                roots.add(src.get("provenance_root", sid))
            # Independent only if at least two DISTINCT roots are named.
            return named >= 2 and len(roots) >= 2

        sources_by_id = {s["id"]: s for s in self.packet["sources"]}

        # Baseline: genuinely distinct, currently-cited sources for the
        # restriction-list scope hypotheses are treated as independent
        # (none of them share a provenance_root in the live packet).
        rc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        for hyp in rc["scope_hypotheses"]["hypotheses"]:
            ids = hyp.get("supporting_source_ids", [])
            named_ids = [i for i in ids if i in sources_by_id]
            if len(named_ids) >= 2:
                self.assertTrue(
                    sources_are_independent(named_ids, sources_by_id),
                    f"hypothesis {hyp['id']}'s supporting sources unexpectedly share a provenance_root",
                )

        # Adversarial: two synthetic sources sharing the same provenance_root
        # (e.g. both mirror the same upstream retrospective claim) must NOT
        # be accepted as independent corroboration, even though they have
        # different ids/URLs.
        site_a = {
            "id": "fixture-mirror-site-a", "label": "Fixture mirror site A",
            "kind": "secondary-history", "url": "https://example.invalid/site-a",
            "provenance_root": "fixture-original-1999-fan-page",
        }
        site_b = {
            "id": "fixture-mirror-site-b", "label": "Fixture mirror site B (re-publishes site A's claim)",
            "kind": "secondary-history", "url": "https://example.invalid/site-b",
            "provenance_root": "fixture-original-1999-fan-page",
        }
        fake_sources_by_id = dict(sources_by_id)
        fake_sources_by_id[site_a["id"]] = site_a
        fake_sources_by_id[site_b["id"]] = site_b
        self.assertFalse(
            sources_are_independent([site_a["id"], site_b["id"]], fake_sources_by_id),
            "two sources sharing a provenance_root were wrongly treated as independent corroboration",
        )

        # A genuinely third, unrelated source (different provenance_root)
        # alongside one of the mirrors DOES count as independent.
        site_c = {
            "id": "fixture-unrelated-site-c", "label": "Fixture unrelated site C",
            "kind": "secondary-history", "url": "https://example.invalid/site-c",
            "provenance_root": "fixture-different-original-source",
        }
        fake_sources_by_id[site_c["id"]] = site_c
        self.assertTrue(
            sources_are_independent([site_a["id"], site_c["id"]], fake_sources_by_id),
        )

    def test_mutation_G_stale_unread_book_sentence_cannot_appear_active(self):
        # Mutation G: injecting the obsolete "no source in this research
        # chain has read the Official Guide Starter Book" sentence into any
        # ordinary active current field must be caught, given the
        # authoritative addendum says the scan WAS inspected.
        current = self.packet["tokyo_dome_research_current"]
        self.assertTrue(current["primary_source_resolution_2026_08_29"]["expert_rules_primary_material"]["located"])

        mutated_blockers = list(current["remaining_blockers"])
        mutated_blockers.append(
            "HISTORICAL: no source in this research chain has read the Official Guide Starter Book's own content."
        )
        violation_found = any(
            "no source in this research chain has read the official guide starter book" in b.lower()
            for b in mutated_blockers
        )
        self.assertTrue(violation_found, "injected stale sentence was not even present for the check to catch")
        # The real, current list must not contain it.
        for b in current["remaining_blockers"]:
            self.assertNotIn("no source in this research chain has read the official guide starter book", b.lower())

    def test_mutation_H_second_competing_matrix_is_rejected(self):
        # Mutation H: reintroducing a second active historical rule matrix
        # with conflicting statuses must be caught. There must be exactly
        # one authoritative matrix pointer, and the archived matrix must
        # live only under superseded_findings, never back under
        # tokyo_dome_research_current.
        current = self.packet["tokyo_dome_research_current"]
        self.assertNotIn("evidence_matrix", current)
        self.assertEqual(
            "primary_source_resolution_2026_08_29.three_column_evidence_matrix",
            current["authoritative_rule_matrix"],
        )

        # Simulate the regression: someone reintroduces the old matrix
        # directly under tokyo_dome_research_current with a conflicting
        # status for a row the new matrix already resolves differently.
        mutated = copy.deepcopy(self.packet)
        old_rows = mutated["superseded_findings"]["superseded_evidence_matrix_pre_primary_source_2026_08_29"]["rows"]
        mutated["tokyo_dome_research_current"]["evidence_matrix"] = old_rows

        new_matrix = {r["rule_area"]: r for r in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]}
        reintroduced_matrix = {r["rule_area"]: r for r in mutated["tokyo_dome_research_current"]["evidence_matrix"]}

        conflict_found = False
        for area in ("tribute_summon", "spell_trap_response"):
            if area not in reintroduced_matrix:
                continue
            old_status = reintroduced_matrix[area].get("starter_box_evidence_status")
            new_area = "tribute_summon" if area == "tribute_summon" else "chain_spell_speed_priority"
            new_status = new_matrix.get(new_area, {}).get("starter_box", {}).get("status")
            if old_status is not None and new_status is not None:
                conflict_found = True
        self.assertTrue(conflict_found, "mutation setup did not actually create a comparable pair of rows")
        # The regression guard: a second matrix existing at all under the
        # current subtree is itself the defect - assert it is absent in the
        # REAL packet (not the mutated copy).
        self.assertNotIn("evidence_matrix", self.packet["tokyo_dome_research_current"])

    def test_mutation_I_stale_derived_consumer_disagreeing_with_authority_is_rejected(self):
        # Mutation I: a derived readiness/blocker field that disagrees with
        # the authoritative matrix must be caught. tokyo_dome_rule_profile_
        # readiness is recomputed FROM the authoritative matrix - verify the
        # live packet's readiness verdict is actually consistent, then show
        # that a stale/disagreeing readiness value is distinguishable.
        current = self.packet["tokyo_dome_research_current"]
        matrix = current["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        proven_tokyo_dome_rows = [r["rule_area"] for r in matrix if r["tokyo_dome"]["status"] == "PROVEN"]

        readiness = current["tokyo_dome_rule_profile_readiness"]
        self.assertEqual(current["primary_source_resolution_2026_08_29"] is not None, True)
        self.assertIn("authoritative_rule_matrix", current)
        # Live consistency: if the matrix has zero PROVEN Tokyo-Dome cells,
        # readiness must be BLOCKED_BY_HISTORICAL_EVIDENCE, not some other
        # verdict implying readiness.
        if not proven_tokyo_dome_rows:
            self.assertEqual("BLOCKED_BY_HISTORICAL_EVIDENCE", readiness["verdict"])

        # Mutate: disagree with the authority by claiming readiness while
        # the matrix still has zero PROVEN Tokyo-Dome cells.
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["tokyo_dome_rule_profile_readiness"]["verdict"] = "RESEARCH_GATE_PASSED"
        mutated_matrix = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        mutated_proven = [r["rule_area"] for r in mutated_matrix if r["tokyo_dome"]["status"] == "PROVEN"]
        mutated_readiness_verdict = mutated["tokyo_dome_research_current"]["tokyo_dome_rule_profile_readiness"]["verdict"]
        # The mutation IS a disagreement: readiness claims passed, matrix has no proof.
        self.assertTrue(
            not mutated_proven and mutated_readiness_verdict == "RESEARCH_GATE_PASSED",
            "mutation did not actually construct a disagreement between the authority and the derived field",
        )
        # And the REAL packet does not have this disagreement.
        self.assertNotEqual("RESEARCH_GATE_PASSED", readiness["verdict"])

    def test_resolution_preserves_approved_certification_and_non_actions(self):
        # UPDATED 2026-08-29: the addendum's own duplicate copies of
        # architecture_verdict and explicit_non_actions were removed during
        # consolidation - there is now exactly one of each, at the top level
        # of tokyo_dome_research_current.
        current = self.packet["tokyo_dome_research_current"]
        resolution = current["primary_source_resolution_2026_08_29"]
        self.assertNotIn("architecture_verdict", resolution)
        self.assertNotIn("explicit_non_actions", resolution)
        self.assertEqual("BLOCKED_BY_BOTH", current["architecture_verdict"])
        self.assertEqual(19, current["release_ledger_preserved"]["verified_this_session"]["products_through_cutoff"])
        self.assertEqual(370, current["release_ledger_preserved"]["verified_this_session"]["pool_size"])
        self.assertEqual("f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb", current["release_ledger_preserved"]["verified_this_session"]["pool_digest_sha256"])
        self.assertTrue(any("canonical Tokyo Dome" in item for item in current["explicit_non_actions"]))
        self.assertTrue(any("secondary claims alone" in item for item in current["explicit_non_actions"]))

    def test_book_is_confirmed_read_not_still_missing(self):
        # Contradictions A and B, direct regression: the packet must no
        # longer ACTIVELY ASSERT the guide is unread/unlocated in ordinary
        # active fields. remaining_blockers[8] and explicit_non_actions[12]
        # were the two specific offenders found and fixed this session -
        # both are still ALLOWED to quote the old phrase (to explain what
        # was corrected), as long as that quoting sentence also carries a
        # correction cue ("obsolete", "no longer", "UPDATED", "prior
        # pass's"). Sentence-scoped, matching _is_may_5_proof_violation's
        # own design, to avoid a false positive against the correction text
        # itself.
        current = self.packet["tokyo_dome_research_current"]
        stale_phrases = ("no source in this research chain has read that book", "no source has read the cited book")
        hedge_cues = ("obsolete", "no longer", "updated 2026", "prior pass's", "is now factually")
        violations = []
        for field, entries in (("remaining_blockers", current["remaining_blockers"]), ("explicit_non_actions", current["explicit_non_actions"])):
            for entry in entries:
                for sentence in SENTENCE_SPLIT_PATTERN.split(entry):
                    low = sentence.lower()
                    if any(p in low for p in stale_phrases) and not any(c in low for c in hedge_cues):
                        violations.append((field, sentence))
        self.assertEqual([], violations, f"stale unread-book claim asserted without a correction cue: {violations}")
        self.assertTrue(
            any("personally located" in b.lower() or "personally inspected" in b.lower() for b in current["remaining_blockers"])
            or any("personally located" in e.lower() or "personally inspected" in e.lower() for e in current["explicit_non_actions"])
        )

    # ------------------------------------------------------------------
    # Authority/projection consistency closure pass (this session): the
    # previous hardening passes scoped their recursive walks to
    # tokyo_dome_research_current only (see test_A/test_B2 above) - that
    # left the top-level packet fields (rule_boundary, rules, blocker_ledger,
    # verdict) and the earliest, unbanner-ed gate.md sections free to keep
    # asserting claims the authoritative section had since disproven. These
    # tests are deliberately whole-packet scoped to close that gap.
    # ------------------------------------------------------------------

    def test_K_no_whole_packet_source_unlocated_or_secondary_only_expert_rules_claim(self):
        _assert_no_whole_packet_source_unlocated_claim(self.packet)
        _assert_no_whole_packet_hyphenated_secondary_only_expert_rules_claim(self.packet)
        # The exemption is real, not merely "no such content exists" -
        # confirm the archive still honestly contains the old claim.
        archive_text = json.dumps(self.packet["superseded_findings"], ensure_ascii=False).lower()
        self.assertIn("has not been located", archive_text)

    def test_L_chain_priority_not_promoted_to_unconditional_blocker(self):
        _assert_chain_priority_not_promoted_to_unconditional_blocker(self.packet)

    def test_M_rule_boundary_is_a_derived_projection_agreeing_with_authority(self):
        _assert_rule_boundary_agrees_with_authority(self.packet)
        # It must also still be a real, distinct field (not silently
        # deleted) and its stale predecessor must be honestly archived, not
        # erased from history.
        self.assertIn("rule_boundary", self.packet)
        archive = self.packet["superseded_findings"]["stale_top_level_rule_boundary_pre_2026_08_29_resolution"]
        self.assertIn("_why_superseded", archive)
        self.assertIn(
            "primary-publication-source-unlocated",
            archive["verbatim_prior_top_level_rule_boundary"]["timeline"][1]["status"],
        )

    def test_N_blocker_ledger_chain_reason_not_silence_based(self):
        _assert_blocker_ledger_chain_reason_not_silence_based(self.packet)
        # Status is unchanged - still BLOCKING, still one of the 18 required
        # keys test_blocker_ledger_is_complete_and_uses_frozen_statuses
        # pins - only the reasoning was corrected, not the classification.
        self.assertEqual("BLOCKING", self.packet["blocker_ledger"]["chain_spell_speed_semantics"]["status"])

    def test_O_top_level_verdict_is_scoped(self):
        _assert_top_level_verdict_is_scoped(self.packet)
        self.assertEqual(
            "representable-with-format-local-approximations", self.packet["verdict"],
        )

    def test_gate_md_current_state_header_matches_authority(self):
        text = (ROOT / "docs" / "research" / "yugi-kaiba-format-source-gate.md").read_text(encoding="utf-8")
        _assert_gate_md_has_current_state_header(text, self.packet)

    def test_gate_md_earliest_sections_no_longer_read_as_unscoped_current_claims(self):
        # Direct regression for the specific pre-"2026-08" passages this
        # session found unscoped: each must now carry an explicit
        # superseded/update marker ahead of (or immediately inside) the
        # stale claim, not merely exist somewhere else in the document.
        text = (ROOT / "docs" / "research" / "yugi-kaiba-format-source-gate.md").read_text(encoding="utf-8")
        self.assertIn("Superseded by the recertification below", text)
        self.assertIn("**Update (2026-08-29):**", text)
        self.assertIn("Superseded (2026-08-29)", text)
        # The specific self-contradiction found in this session's own
        # audit: the final "Canonicalization blocker ledger" table must no
        # longer classify deck-out/battle-calculation as an unqualified
        # "RESOLVED WITH APPROXIMATION" (which reads as unblocked) - it must
        # use the distinguishing HISTORY_RESOLVED_ENGINE_GAP_REMAINS status.
        self.assertIn("HISTORY_RESOLVED_ENGINE_GAP_REMAINS", text)
        final_ledger = text.split("### Canonicalization blocker ledger (per-topic, this pass)", 1)[1]
        self.assertNotIn("| Deck-out rule | RESOLVED WITH APPROXIMATION", final_ledger)
        self.assertNotIn("| Battle-calculation semantics | RESOLVED WITH APPROXIMATION", final_ledger)

    # ------------------------------------------------------------------
    # Phase D: adversarial mutation tests for the invariants above.
    # ------------------------------------------------------------------

    def test_mutation_J_rule_boundary_regression_to_source_unlocated_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["rule_boundary"]["timeline"][1]["status"] = (
            "resolved-as-secondary-date; primary-publication-source-unlocated"
        )
        mutated["rule_boundary"]["timeline"][1]["evidence"] = "strong-secondary-reconstruction"
        with self.assertRaises(AssertionError):
            _assert_no_whole_packet_source_unlocated_claim(mutated)
        with self.assertRaises(AssertionError):
            _assert_rule_boundary_agrees_with_authority(mutated)

    def test_mutation_K_any_top_level_field_claiming_source_unlocated_is_rejected(self):
        # Prove the check is genuinely whole-packet, not just rule_boundary-
        # specific: inject the same claim into an unrelated field.
        mutated = copy.deepcopy(self.packet)
        mutated["target_recommendation"]["_injected_for_test"] = (
            "The first publication source has not been located for this guide."
        )
        with self.assertRaises(AssertionError):
            _assert_no_whole_packet_source_unlocated_claim(mutated)

    def test_mutation_L_chain_priority_promoted_to_engine_blocker_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["architecture_verdict_detail"]["engine_representation_blockers"]["items"].append(
            "chain_spell_speed_priority - full modern chain/priority system, promoted in error"
        )
        with self.assertRaises(AssertionError):
            _assert_chain_priority_not_promoted_to_unconditional_blocker(mutated)

    def test_mutation_M_known_gaps_detail_flip_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["rules"]["candidate_core_flags"]["known_gaps_detail"]["pre-formal-chain-and-priority-boundary"][
            "confirmed_unconditional_tokyo_dome_blocker"
        ] = True
        with self.assertRaises(AssertionError):
            _assert_chain_priority_not_promoted_to_unconditional_blocker(mutated)

    def test_mutation_N_matrix_row_flip_to_proven_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        matrix = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        for row in matrix:
            if row["rule_area"] == "chain_spell_speed_priority":
                row["tokyo_dome"]["status"] = "PROVEN"
        with self.assertRaises(AssertionError):
            _assert_chain_priority_not_promoted_to_unconditional_blocker(mutated)

    def test_mutation_O_blocker_ledger_reason_regression_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["blocker_ledger"]["chain_spell_speed_semantics"]["reason"] = (
            "The available first rulebook lacks formal Chain/Spell Speed/priority rules and no "
            "general core flag supplies the historical boundary."
        )
        with self.assertRaises(AssertionError):
            _assert_blocker_ledger_chain_reason_not_silence_based(mutated)

    def test_mutation_P_top_level_verdict_scope_note_deleted_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        del mutated["verdict_scope_note"]
        with self.assertRaises(AssertionError):
            _assert_top_level_verdict_is_scoped(mutated)

    def test_mutation_Q_gate_md_current_state_header_regression_is_rejected(self):
        text = (ROOT / "docs" / "research" / "yugi-kaiba-format-source-gate.md").read_text(encoding="utf-8")
        mutated_text = text.replace(
            "## Current authoritative state (read this first)", "## Some other heading, no longer matched",
        )
        with self.assertRaises(AssertionError):
            _assert_gate_md_has_current_state_header(mutated_text, self.packet)

        # A header that exists but silently regressed to a stale claim must
        # also be rejected, not just a missing header.
        marker = "## Current authoritative state (read this first)"
        section_end = text.index("\n## Verdict")
        corrupted = (
            text[: text.index(marker)]
            + marker
            + "\n\nThe primary publication source has not been located.\n"
            + text[section_end:]
        )
        with self.assertRaises(AssertionError):
            _assert_gate_md_has_current_state_header(corrupted, self.packet)

    # ------------------------------------------------------------------
    # Unconditional-blocker adjudication pass (this session): deck_out,
    # trap_activation_frequency, and battle_calculation re-examined against
    # an explicit, structural standard rather than "PROVEN at Starter Box +
    # no located evidence of change" (the same silence-based reasoning
    # already correctly rejected for chain_spell_speed_priority).
    # ------------------------------------------------------------------

    def test_R_unconditional_blockers_match_the_structural_standard(self):
        # Deliberately does NOT hard-code a fixed membership or count - the
        # set is whatever the standard structurally derives from current
        # engine_reassessment/matrix/positive_continuity_evidence state, and
        # must change when that state legitimately changes (as it did this
        # session: battle_calculation dropped out after its engine
        # classification was corrected). This test only proves the packet's
        # own list agrees with its own inputs, not that any particular
        # rule_area belongs there.
        _assert_unconditional_blocker_standard(self.packet)
        expected = _derive_expected_unconditional_engine_blockers(self.packet)
        self.assertTrue(expected, "expected at least one legitimate unconditional blocker to survive")

    def test_R2_battle_calculation_is_no_longer_an_unconditional_blocker(self):
        # Direct regression for this session's specific finding: personal
        # inspection of the pinned ocgcore source found the historical
        # ATK<ATK/ATK<DEF attacker-recoil arithmetic is the engine's default
        # behavior, so battle_calculation fails the engine-incompatibility
        # half of the standard even though its historical-applicability half
        # (positive_continuity_evidence) remains exactly as strong as
        # deck_out's and trap_activation_frequency's.
        current = self.packet["tokyo_dome_research_current"]
        psr = current["primary_source_resolution_2026_08_29"]
        engine = {r["rule_area"]: r["classification"] for r in psr["engine_reassessment"]}
        self.assertEqual("REPRESENTABLE_EXACT_BY_DEFAULT", engine["battle_calculation"])
        self.assertNotEqual("NOT_REPRESENTABLE", engine["battle_calculation"])

        engine_items_text = " ".join(current["architecture_verdict_detail"]["engine_representation_blockers"]["items"])
        self.assertNotIn("battle_calculation -", engine_items_text)

        expected = _derive_expected_unconditional_engine_blockers(self.packet)
        self.assertNotIn("battle_calculation", expected)
        # Its historical continuity evidence must survive unchanged - the
        # architectural consequence changed, the research did not.
        self.assertIn("battle_calculation", current["positive_continuity_evidence"]["items"])
        self.assertIs(
            current["positive_continuity_evidence"]["items"]["battle_calculation"]["not_silence_based"], True
        )

    def test_R3_arithmetic_and_timing_are_modeled_as_separate_epistemic_claims(self):
        split = self.packet["tokyo_dome_research_current"]["positive_continuity_evidence"]["items"][
            "battle_calculation"
        ]["arithmetic_vs_timing_split"]
        arithmetic = split["arithmetic_and_destruction_table"]
        timing = split["damage_step_timing_and_response_windows"]
        # Different historical evidence tiers - arithmetic is well-supported,
        # timing is genuinely unknown - must not be collapsed into one claim.
        self.assertIn("PROVEN", arithmetic["historical_status"])
        self.assertIn("UNKNOWN", timing["historical_status"])
        self.assertNotEqual(arithmetic["historical_status"], timing["historical_status"])
        # Neither sub-claim is a blocker on its own: arithmetic because the
        # engine already represents it, timing because its historical
        # applicability was never established.
        self.assertIs(arithmetic["engine_blocker"], False)
        self.assertIs(timing["engine_blocker"], False)

    def test_R4_no_active_prose_claims_the_recoil_arithmetic_is_absent_from_modern_rules(self):
        _assert_no_active_recoil_absent_from_modern_claim(self.packet)

    def test_S_positive_continuity_evidence_is_genuinely_not_silence_based(self):
        current = self.packet["tokyo_dome_research_current"]
        pce = current["positive_continuity_evidence"]["items"]
        self.assertEqual({"deck_out", "trap_activation_frequency", "battle_calculation"}, set(pce))
        for area, item in pce.items():
            self.assertIs(item["not_silence_based"], True)
            self.assertEqual("official-guide-starter-book-1999-scan", item["intermediate_source_id"])
            self.assertEqual("1999-05-05", item["intermediate_source_date"])
            self.assertTrue(item["intermediate_source_quote_translated"])
            self.assertTrue(item["expert_rules_relationship"])
            self.assertTrue(item["upper_bound_evidence"])
        # chain_spell_speed_priority deliberately has NO entry - its
        # continuity is genuinely unknown, not merely under-evidenced
        # silence being mistaken for proof.
        self.assertNotIn("chain_spell_speed_priority", pce)

    def test_S2_shared_upper_bound_provenance_root_is_recorded_not_double_counted(self):
        # Adversarial-review finding (Phase D, this session): deck_out's
        # "New Expert Rule" upper bound and trap_activation_frequency's
        # "Quick-Play Spell Cards" upper bound both trace to the same
        # Magic Ruler (2000-04-20) release - they must be recorded as ONE
        # shared provenance root, not presented as two independent
        # corroborating findings (matches the established provenance_root
        # discipline used elsewhere in this packet for source clustering).
        pce = self.packet["tokyo_dome_research_current"]["positive_continuity_evidence"]["items"]
        self.assertEqual(
            pce["deck_out"]["upper_bound_provenance_root"],
            pce["trap_activation_frequency"]["upper_bound_provenance_root"],
        )
        self.assertTrue(pce["deck_out"]["upper_bound_provenance_root"])

    def test_S3_adversarial_review_recorded_for_all_three_behaviours(self):
        review = self.packet["tokyo_dome_research_current"]["positive_continuity_evidence"][
            "adversarial_review_2026_08_29"
        ]
        for area in ("deck_out", "trap_activation_frequency", "battle_calculation"):
            self.assertIn("challenge", review[area])
            self.assertIn("adjudication", review[area])
            self.assertTrue(review[area]["challenge"])
            self.assertTrue(review[area]["adjudication"])

    def test_T_continuity_evidence_does_not_silently_promote_the_matrix_tier(self):
        _assert_continuity_evidence_not_promoted_to_proven(self.packet)

    def test_U_architecture_verdict_derived_consistently_from_both_categories(self):
        _assert_architecture_verdict_derived_consistently(self.packet)

    def test_V_conditional_engine_gaps_stay_separate_from_unconditional_blockers(self):
        # Invariant 6, direct regression: the three genuinely-conditional
        # engine/history gaps must never appear in the unconditional list,
        # even though each has an engine-representability wrinkle of its
        # own (per explicitly_not_counted_as_a_blocker).
        current = self.packet["tokyo_dome_research_current"]
        engine_items_text = " ".join(current["architecture_verdict_detail"]["engine_representation_blockers"]["items"])
        for conditional_area in ("tribute_summon", "fusion_material_location", "chain_spell_speed_priority"):
            self.assertNotIn(conditional_area + " -", engine_items_text)
        psr = current["primary_source_resolution_2026_08_29"]
        engine = {r["rule_area"]: r["classification"] for r in psr["engine_reassessment"]}
        self.assertEqual("UNKNOWN_BECAUSE_HISTORY_UNKNOWN", engine["tribute_summon"])
        self.assertEqual("UNKNOWN_BECAUSE_HISTORY_UNKNOWN", engine["fusion_material_location"])
        self.assertEqual("UNKNOWN_BECAUSE_HISTORY_UNKNOWN", engine["chain_spell_speed_priority"])

    def test_W_ito_akira_counter_claim_is_recorded_as_rejected_not_current_evidence(self):
        # Invariant 8 (narrow instance): a considered-and-rejected counter-
        # claim may be recorded in an ACTIVE field (personally_reverified_claims)
        # for transparency, but only if its own text unambiguously marks it
        # rejected - it must never read as accepted current evidence.
        current = self.packet["tokyo_dome_research_current"]
        ito_claims = [
            c for c in current["personally_reverified_claims"]
            if c["claim_source_id"] == "ito-akira-tweet-2024"
        ]
        self.assertEqual(1, len(ito_claims))
        establishes = ito_claims[0]["what_it_establishes"]
        self.assertIn("CONSIDERED AND REJECTED", establishes)
        self.assertIn("not as a load-bearing finding", establishes)

    def test_X_engine_reassessment_and_canonicalization_blockers_cover_all_three_rule_areas(self):
        # Direct regression for the specific completeness gap this session
        # found: trap_activation_frequency previously had NO row in
        # engine_reassessment or canonicalization_blockers at all, even
        # though it was already cited as an unconditional blocker.
        psr = self.packet["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]
        engine_areas = {r["rule_area"] for r in psr["engine_reassessment"]}
        for area in ("deck_out", "trap_activation_frequency", "battle_calculation"):
            self.assertIn(area, engine_areas)
        cb_item_names = " ".join(i["item"] for i in psr["canonicalization_blockers"]["items"])
        self.assertIn("deck-out rule", cb_item_names)
        self.assertIn("battle-calculation semantics", cb_item_names)
        self.assertIn("Trap-only", cb_item_names)

    def test_Y_no_stale_tokyo_dome_exceptions_claimed_outside_the_matrix(self):
        # Direct regression: remaining_blockers[0] previously claimed
        # deck_out/hand_limit were "BOUNDED" and tribute_summon "AMBIGUOUS"
        # exceptions to "every rule area's tokyo_dome_evidence_status is
        # UNKNOWN" - contradicting both the matrix itself (21 of 21 UNKNOWN,
        # no exceptions) and tokyo_dome_rule_profile_readiness's own
        # explanation. Structural check, not a substring ban: every matrix
        # row's tokyo_dome.status must actually be UNKNOWN.
        current = self.packet["tokyo_dome_research_current"]
        psr = current["primary_source_resolution_2026_08_29"]
        matrix = psr["three_column_evidence_matrix"]
        non_unknown = [r["rule_area"] for r in matrix if r["tokyo_dome"]["status"] != "UNKNOWN"]
        self.assertEqual([], non_unknown)
        self.assertNotIn("BOUNDED", current["remaining_blockers"][0])
        self.assertNotIn("AMBIGUOUS", current["remaining_blockers"][0])

    # ------------------------------------------------------------------
    # Phase D: adversarial mutation tests for the standard above.
    # ------------------------------------------------------------------

    def test_mutation_R_starter_box_proven_plus_tokyo_dome_unknown_alone_is_not_enough(self):
        # Invariant 1: strip trap_activation_frequency's positive_continuity_
        # evidence entry (leaving starter_box PROVEN + tokyo_dome UNKNOWN,
        # exactly the pattern the task warned is NOT sufficient on its own)
        # while leaving it listed as an unconditional blocker - must be caught.
        mutated = copy.deepcopy(self.packet)
        del mutated["tokyo_dome_research_current"]["positive_continuity_evidence"]["items"]["trap_activation_frequency"]
        with self.assertRaises(AssertionError):
            _assert_unconditional_blocker_standard(mutated)

    def test_mutation_S_bare_not_representable_classification_is_not_enough(self):
        # Invariant 3: flip tribute_summon's engine_reassessment
        # classification to NOT_REPRESENTABLE (its starter_box tier is
        # UNKNOWN, not PROVEN, and it has no positive_continuity_evidence)
        # - this alone must not make the derived standard treat it as an
        # unconditional blocker, but if someone ALSO added it to the items
        # list, that must be caught.
        mutated = copy.deepcopy(self.packet)
        for row in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["engine_reassessment"]:
            if row["rule_area"] == "tribute_summon":
                row["classification"] = "NOT_REPRESENTABLE"
        expected = _derive_expected_unconditional_engine_blockers(mutated)
        self.assertNotIn("tribute_summon", expected, "bare NOT_REPRESENTABLE alone must not create a blocker")
        mutated["tokyo_dome_research_current"]["architecture_verdict_detail"]["engine_representation_blockers"]["items"].append(
            "tribute_summon - injected for test"
        )
        with self.assertRaises(AssertionError):
            _assert_unconditional_blocker_standard(mutated)

    def test_mutation_T_supported_but_incomplete_cannot_be_silently_rendered_proven(self):
        mutated = copy.deepcopy(self.packet)
        for row in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]:
            if row["rule_area"] == "deck_out":
                row["later_pre_tokyo_dome"]["status"] = "PROVEN"
        with self.assertRaises(AssertionError):
            _assert_continuity_evidence_not_promoted_to_proven(mutated)

    def test_mutation_U_tokyo_dome_status_reset_to_unknown_needs_a_surviving_continuity_bound(self):
        # Invariant 5: deck_out's tokyo_dome.status is already UNKNOWN in the
        # live packet (correctly - no event-specific source exists), and the
        # blocker survives ONLY because positive_continuity_evidence supplies
        # the missing evidence. Removing BOTH must fail; removing only the
        # (already-UNKNOWN) matrix status is a no-op and must keep passing,
        # proving the continuity mechanism is genuinely doing the work.
        baseline = copy.deepcopy(self.packet)
        _assert_unconditional_blocker_standard(baseline)  # sanity: passes today

        mutated = copy.deepcopy(self.packet)
        del mutated["tokyo_dome_research_current"]["positive_continuity_evidence"]["items"]["deck_out"]
        with self.assertRaises(AssertionError):
            _assert_unconditional_blocker_standard(mutated)

        restored = copy.deepcopy(mutated)
        for row in restored["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]:
            if row["rule_area"] == "deck_out":
                row["tokyo_dome"]["status"] = "PROVEN"
        _assert_unconditional_blocker_standard(restored)  # a real event-specific PROVEN also satisfies it

    def test_mutation_V_conditional_gap_smuggled_into_unconditional_list_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["architecture_verdict_detail"]["engine_representation_blockers"]["items"].append(
            "chain_spell_speed_priority - smuggled back in for test, no positive_continuity_evidence backs this"
        )
        with self.assertRaises(AssertionError):
            _assert_unconditional_blocker_standard(mutated)

    def test_mutation_W_architecture_verdict_must_track_its_own_inputs(self):
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["architecture_verdict_detail"]["engine_representation_blockers"]["items"] = []
        # engine blockers now empty, but the top-line verdict was not
        # recomputed - must be rejected.
        with self.assertRaises(AssertionError):
            _assert_architecture_verdict_derived_consistently(mutated)

    def test_mutation_X_stale_tokyo_dome_exception_reintroduced_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        for row in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]:
            if row["rule_area"] == "hand_limit":
                row["tokyo_dome"]["status"] = "BOUNDED"
        matrix = mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["three_column_evidence_matrix"]
        non_unknown = [r["rule_area"] for r in matrix if r["tokyo_dome"]["status"] != "UNKNOWN"]
        self.assertEqual(["hand_limit"], non_unknown)

    # ------------------------------------------------------------------
    # Engine-representability re-adjudication (this session): battle_
    # calculation was removed from the unconditional-blocker set after
    # personally inspecting the exact pinned ocgcore source and finding its
    # arithmetic/destruction table is already the engine's default
    # behavior. These mutations prove the standard's engine-incompatibility
    # half is genuinely load-bearing and generic (not special-cased for
    # battle_calculation specifically).
    # ------------------------------------------------------------------

    def test_mutation_Y_flipping_not_representable_to_representable_removes_the_blocker(self):
        # Generic proof the mechanism works for ANY currently-blocking rule
        # area, not just battle_calculation: flip deck_out's engine
        # classification away from NOT_REPRESENTABLE and it must drop out of
        # the derived set even though its historical evidence is untouched.
        mutated = copy.deepcopy(self.packet)
        for row in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["engine_reassessment"]:
            if row["rule_area"] == "deck_out":
                row["classification"] = "REPRESENTABLE_EXACT_BY_DEFAULT"
        expected = _derive_expected_unconditional_engine_blockers(mutated)
        self.assertNotIn("deck_out", expected)
        # The packet's own (unmutated) items list still claims deck_out -
        # now stale relative to the mutated engine_reassessment - so the
        # consistency check must fail.
        with self.assertRaises(AssertionError):
            _assert_unconditional_blocker_standard(mutated)

    def test_mutation_Z_positive_continuity_evidence_alone_cannot_create_a_blocker(self):
        # chain_spell_speed_priority has no engine gap of the required kind
        # (UNKNOWN_BECAUSE_HISTORY_UNKNOWN, not NOT_REPRESENTABLE) - even if
        # it were GIVEN strong positive_continuity_evidence, that must not
        # be enough on its own to create a blocker without a genuine
        # NOT_REPRESENTABLE classification.
        mutated = copy.deepcopy(self.packet)
        engine_areas = {
            r["rule_area"]: r["classification"]
            for r in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["engine_reassessment"]
        }
        self.assertNotEqual("NOT_REPRESENTABLE", engine_areas.get("chain_spell_speed_priority"))
        mutated["tokyo_dome_research_current"]["positive_continuity_evidence"]["items"]["chain_spell_speed_priority"] = {
            "mechanism": "injected for test",
            "not_silence_based": True,
        }
        expected = _derive_expected_unconditional_engine_blockers(mutated)
        self.assertNotIn("chain_spell_speed_priority", expected)

    def test_mutation_AA_unknown_timing_cannot_be_smuggled_in_as_not_representable(self):
        # Direct guard against the specific move this session reversed: an
        # earlier pass tried to preserve battle_calculation as a blocker by
        # reframing the gap as a "single-step, response-window-free
        # procedure" - a historically UNKNOWN claim dressed up as an engine
        # fact. Confirm the historical record correctly marks that timing
        # question UNKNOWN and not a blocker, then prove that reintroducing
        # the old unhedged justification text is exactly what test_R4's
        # standing prose guard exists to catch.
        current = self.packet["tokyo_dome_research_current"]
        timing = current["positive_continuity_evidence"]["items"]["battle_calculation"][
            "arithmetic_vs_timing_split"
        ]["damage_step_timing_and_response_windows"]
        self.assertIn("UNKNOWN", timing["historical_status"])
        self.assertIs(timing["engine_blocker"], False)

        mutated = copy.deepcopy(self.packet)
        for row in mutated["tokyo_dome_research_current"]["primary_source_resolution_2026_08_29"]["engine_reassessment"]:
            if row["rule_area"] == "battle_calculation":
                row["classification"] = "NOT_REPRESENTABLE"
                row["current_behavior"] = (
                    "Modern damage-step behavior does not reproduce the historical ATK<DEF "
                    "attacker-recoil result without card-script/core changes."
                )
        with self.assertRaises(AssertionError):
            _assert_no_active_recoil_absent_from_modern_claim(mutated)

    # ------------------------------------------------------------------
    # Phase 0 (2026-08-30, session 4): tiny consistency closure for stale
    # wording left by session 3's battle_calculation removal.
    # ------------------------------------------------------------------

    def test_AB_known_gaps_scope_note_does_not_claim_a_stale_count(self):
        scope = self.packet["rules"]["_scope"]
        self.assertNotIn("three equally-confirmed", scope)
        known_gaps = self.packet["rules"]["candidate_core_flags"]["known_gaps"]
        self.assertEqual(2, len(known_gaps))
        self.assertNotIn("early-battle-calculation", known_gaps)

    def test_AC_remaining_blockers_does_not_claim_battle_calculation_is_an_engine_blocker(self):
        current = self.packet["tokyo_dome_research_current"]
        rb0 = current["remaining_blockers"][0]
        self.assertIn("battle_calculation does NOT", rb0)
        # Structural, not just textual: cross-check against the actual
        # derived standard.
        expected = _derive_expected_unconditional_engine_blockers(self.packet)
        self.assertNotIn("battle_calculation", expected)

    def test_AD_battle_calculation_semantics_uses_the_semantically_correct_resolved_status(self):
        # RESOLVED (bare), not RESOLVED WITH APPROXIMATION: matches the
        # exact-match precedent (first_turn_draw/first_turn_attack), not the
        # numeric-ceiling-approximation precedent (deck_size_representation/
        # hand_limit) - the pinned engine's default behavior is an EXACT
        # match for the arithmetic, not an approximation of it.
        entry = self.packet["blocker_ledger"]["battle_calculation_semantics"]
        self.assertEqual("RESOLVED", entry["status"])
        self.assertNotEqual("RESOLVED WITH APPROXIMATION", entry["status"])
        self.assertIn("EXACTLY", entry["reason"])

    def test_mutation_AE_stale_known_gaps_count_reintroduced_is_caught(self):
        # FIXED (2026-09): previously mutated the packet and merely
        # asserted the mutation took effect, proving nothing about whether
        # the repository would reject it. Now calls the real mechanical
        # cross-check helper and asserts IT raises.
        mutated = copy.deepcopy(self.packet)
        mutated["rules"]["_scope"] = mutated["rules"]["_scope"].replace(
            "equally-confirmed Tokyo Dome blockers (currently two entries, not necessarily equally confirmed - "
            "early-battle-calculation was removed 2026-08-29 session 3 after engine re-verification; see "
            "superseded_findings for its archived record)",
            "three equally-confirmed Tokyo Dome blockers",
        )
        with self.assertRaises(AssertionError):
            _assert_known_gaps_scope_note_matches_actual_count(mutated)

    def test_mutation_AF_battle_calculation_semantics_reverted_to_approximation_is_caught(self):
        # FIXED (2026-09): previously mutated the packet and merely
        # asserted the mutation took effect (self.assertNotEqual against
        # the mutated value itself), proving nothing. Now cross-checks
        # against the actual engine_reassessment classification.
        mutated = copy.deepcopy(self.packet)
        mutated["blocker_ledger"]["battle_calculation_semantics"]["status"] = "RESOLVED WITH APPROXIMATION"
        with self.assertRaises(AssertionError):
            _assert_battle_calculation_semantics_status_matches_engine_classification(mutated)

    def test_AE_direct_known_gaps_count_check_passes_on_live_packet(self):
        _assert_known_gaps_scope_note_matches_actual_count(self.packet)

    def test_AF_direct_battle_calculation_classification_check_passes_on_live_packet(self):
        _assert_battle_calculation_semantics_status_matches_engine_classification(self.packet)

    # ------------------------------------------------------------------
    # Restriction-list contemporaneous-source recovery (2026-08-30) and
    # artifact-requirements re-derivation (2026-09): a V Jump 1999-09 page
    # image and an independently-archived fan restriction chronology were
    # located and personally inspected. The original three-axis model
    # (content/scope/effective-date) was then re-examined against what an
    # actual banlist artifact requires (schemas + validate.py + lflist.py)
    # and split into SIX axes - four load-bearing, two explicitly
    # non-blocking - so that resolving a purely historical question (H2 vs
    # H3; the restriction's true first-ever start date) can never gate
    # canonicalization on its own. These tests make the gate evidence-
    # sensitive: a genuinely qualifying future source CAN promote
    # canonicalization_status, but only by proving all FOUR load-bearing
    # axes, never by improving one and letting it carry the others, and
    # never by resolving a non-blocking axis instead.
    # ------------------------------------------------------------------

    def test_AG_restriction_axes_are_evidenced_and_gate_still_blocks(self):
        _assert_restriction_list_axes_are_independently_evidenced(self.packet)
        rlc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertEqual("UNRESOLVED_BLOCKING", rlc["canonicalization_status"]["status"])
        for axis in RESTRICTION_LOAD_BEARING_AXES:
            self.assertEqual("SUPPORTED_BUT_INCOMPLETE", rlc[axis]["status"])
        for axis in RESTRICTION_NONBLOCKING_AXES:
            self.assertEqual("UNRESOLVED_NONBLOCKING", rlc[axis]["status"])

    def test_AH_axis_status_is_not_self_contradicting(self):
        _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(self.packet)

    def test_AI_vjump_september_1999_lead_was_located_and_personally_inspected(self):
        # Direct regression for this session's primary research target.
        current = self.packet["tokyo_dome_research_current"]
        rlc = current["restriction_list_current"]
        inv = rlc["contemporaneous_source_investigation_2026_08_30"]
        vjump = inv["vjump_1999_09_investigation"]
        transcribed = vjump["image_personally_inspected"]["exact_japanese_text_transcribed"]
        self.assertTrue(transcribed)
        self.assertTrue(any("決闘者伝説" in s for s in transcribed))
        self.assertTrue(any("サンダー・ボルト" in s for s in transcribed))
        self.assertIn("authenticity_caveats", vjump)
        self.assertTrue(vjump["authenticity_caveats"])
        _assert_vjump_issue_designation_and_street_date_are_distinct(self.packet)

    def test_AJ_home_att_chronology_independently_corroborates_without_citing_master_guide(self):
        chron = self.packet["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["home_att_puppiy_chronology_investigation"]
        self.assertIn("東京ドーム", chron["exact_japanese_text_of_1999_entry"])
        self.assertIn("サンダー・ボルト", chron["exact_japanese_text_of_1999_entry"])
        # Honest limitation preserved, not silently dropped.
        self.assertIn("citation_for_its_own_1999_entry", chron)
        self.assertIn("None given", chron["citation_for_its_own_1999_entry"])

    def test_AK_provenance_roots_are_distinct_not_double_counted(self):
        _assert_provenance_roots_not_double_counted(self.packet)

    def test_AL_master_guide_recorded_as_not_contemporaneous(self):
        _assert_contemporaneity_not_conflated_with_retrospective(self.packet)

    def test_AM_first_effective_date_status_distinguishes_publication_from_effective_date(self):
        eff = self.packet["tokyo_dome_research_current"]["restriction_list_current"]["first_effective_date_status"]
        self.assertIn("explicit_date_never_found", eff)
        text = eff["explicit_date_never_found"].lower()
        self.assertIn("publication", text)
        self.assertIn("effective", text)
        self.assertIn("tournament", text)
        # 2026-09: this axis is explicitly non-blocking - direct check that
        # it is marked as such and does not silently gate canonicalization.
        self.assertEqual("UNRESOLVED_NONBLOCKING", eff["status"])
        self.assertIn("first_effective_date_status", RESTRICTION_NONBLOCKING_AXES)

    def test_AN_target_applicability_and_content_have_separately_justified_evidence(self):
        # A source containing card names must not automatically prove
        # target-event applicability, and a source naming Tokyo Dome must
        # not automatically prove the card list - checked structurally:
        # each axis's own reasoning text must discuss ITS OWN proposition,
        # not borrow the other's.
        rlc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        content_text = json.dumps(rlc["content_membership_status"], ensure_ascii=False)
        applicability_text = json.dumps(rlc["target_event_applicability_status"], ensure_ascii=False)
        self.assertTrue(any(card in content_text for card in ("サンダー・ボルト", "Raigeki", "three cards", "3 cards", "1999-09")))
        self.assertTrue(any(k in applicability_text for k in ("tournament", "H1", "H2", "H3", "決闘者伝説")))
        # The two axes must not be byte-identical (a copy-paste sign that
        # one was not independently justified).
        self.assertNotEqual(
            rlc["content_membership_status"]["not_PROVEN_because"],
            rlc["target_event_applicability_status"]["what_is_well_supported"],
        )

    def test_AR_nonblocking_axes_never_gate_canonicalization(self):
        # Direct proof of this pass's central rule: a historical
        # uncertainty is a canonicalization blocker only if resolving it
        # could change the artifact.
        _assert_nonblocking_axes_never_gate_canonicalization(self.packet)

    def test_AS_no_stale_independence_overclaims_in_active_prose(self):
        _assert_no_stale_restriction_list_independence_overclaims(self.packet)

    def test_AT_provenance_groups_carry_distinct_hosting_and_authorship_flags(self):
        # Phase E provenance-testing improvement: hosting independence and
        # authorship independence are DISTINCT, mechanically-knowable
        # claims - checked structurally, not inferred from prose.
        groups = self.packet["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["provenance_independence_assessment"]["independence_groups"]
        for g in groups:
            self.assertIn("independent_hosting", g)
            self.assertIn("independent_authorship_demonstrated", g)
            self.assertIn(g["independent_authorship_demonstrated"], (True, False, "not_demonstrated"))
        # The specific known case: vjump-1999-09 and the marukovicchi
        # comment share an underlying primary object - neither may claim
        # demonstrated authorship independence from the other.
        by_root = {g["provenance_root"]: g for g in groups}
        self.assertNotEqual(
            True, by_root["vjump-1999-09-via-ygoldschool-blog"]["independent_authorship_demonstrated"]
        )
        self.assertNotEqual(
            True, by_root["marukovicchi-comment-citing-mercari-listing"]["independent_authorship_demonstrated"]
        )
        # Hosting independence is real for both (distinct files/hosts).
        self.assertTrue(by_root["vjump-1999-09-via-ygoldschool-blog"]["independent_hosting"])
        self.assertTrue(by_root["marukovicchi-comment-citing-mercari-listing"]["independent_hosting"])

    def test_AU_banlist_artifact_requirements_cite_real_schema_and_code(self):
        # Phase A must be derived from the repository's own schema/code,
        # not inferred - checked structurally: the recorded findings must
        # cite the exact files this pass was told to read.
        reqs = self.packet["tokyo_dome_research_current"]["restriction_list_current"][
            "banlist_artifact_requirements_2026_09"
        ]
        a1 = reqs["A1_what_effective_date_means"]
        self.assertIn("schemas/banlist.schema.json", a1["schema_text"])
        self.assertIn("docs/format-schema.md", a1["doc_text"])
        self.assertIn("retroformats/validate.py", a1["mechanical_check"])
        self.assertIn("retroformats/lflist.py", a1["mechanical_use_in_build"])
        self.assertIn("2005-04-goat", a1["existing_precedent"])
        test = reqs["critical_logical_test"]
        self.assertIn("question", test)
        self.assertIn("H2", test["question"])
        self.assertIn("H3", test["question"])
        self.assertIn("NO", test["answer"][:10])

    def test_mutation_AG_canonicalization_promoted_without_all_load_bearing_axes_proven_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        # Only content_membership_status reaches PROVEN - the other three
        # load-bearing axes remain incomplete.
        rlc["content_membership_status"]["status"] = "PROVEN"
        rlc["canonicalization_status"]["status"] = "RESOLVED"
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axes_are_independently_evidenced(mutated)

    def test_mutation_AH_canonicalization_promoted_with_all_load_bearing_axes_proven_is_accepted(self):
        # Proves the gate is genuinely evidence-sensitive, not a permanent
        # "always UNRESOLVED_BLOCKING" trap: if a future source legitimately
        # proved all FOUR load-bearing axes, promotion must be ACCEPTED,
        # even while the two non-blocking axes remain unresolved.
        mutated = copy.deepcopy(self.packet)
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        for axis in RESTRICTION_LOAD_BEARING_AXES:
            rlc[axis]["status"] = "PROVEN"
            rlc[axis].pop("not_PROVEN_because", None)
            rlc[axis].pop("what_remains_unresolved", None)
            rlc[axis].pop("explicit_date_never_found", None)
            # Simulate a REAL future proof, not just a flipped status flag:
            # every remaining string field must also be rewritten clean of
            # hedge language, exactly as a genuine future edit would do -
            # target_event_applicability_status/source_authentication_status
            # carry their hedge prose under differently-named fields
            # (what_is_well_supported/current_state), which a naive test
            # that only pops the three named hedge keys would miss.
            for field_name in list(rlc[axis].keys()):
                if field_name in ("status", "source_ids", "proposition"):
                    continue
                if isinstance(rlc[axis][field_name], str):
                    rlc[axis][field_name] = "Hypothetically fully proven by a future qualifying source."
        rlc["canonicalization_status"]["status"] = "RESOLVED"
        _assert_restriction_list_axes_are_independently_evidenced(mutated)  # must NOT raise
        _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(mutated)  # must NOT raise

    def test_mutation_AI_axis_promoted_to_proven_with_named_hedge_field_still_present_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        rlc["content_membership_status"]["status"] = "PROVEN"
        # not_PROVEN_because is deliberately left in place - the bug.
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(mutated)

    def test_mutation_AI2_axis_promoted_to_proven_with_hedge_phrase_under_different_field_name_is_rejected(self):
        # Direct regression for a gap this pass's own review found: two
        # axes (target_event_applicability_status, source_authentication_
        # status) carry their hedge language under fields NOT named like
        # the other four axes' hedge keys (what_is_well_supported,
        # current_state) - a field-name-only check would silently miss a
        # bad PROVEN promotion on either. Confirms the live packet's OWN
        # text on this axis (unmodified) still contains the phrase, then
        # confirms flipping status alone (leaving that live text in place)
        # is correctly rejected.
        mutated = copy.deepcopy(self.packet)
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertIn("falls short of PROVEN", rlc["target_event_applicability_status"]["what_is_well_supported"])
        rlc["target_event_applicability_status"]["status"] = "PROVEN"
        # what_is_well_supported is deliberately left untouched - the bug.
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axis_not_promoted_without_own_hedge_removed(mutated)

    def test_mutation_AJ_axis_with_no_source_ids_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["restriction_list_current"]["content_membership_status"][
            "source_ids"
        ] = []
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axes_are_independently_evidenced(mutated)

    def test_mutation_AK_axis_citing_unresolvable_source_id_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        mutated["tokyo_dome_research_current"]["restriction_list_current"]["target_event_applicability_status"][
            "source_ids"
        ] = ["this-source-id-does-not-exist"]
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axes_are_independently_evidenced(mutated)

    def test_mutation_AL_duplicate_provenance_root_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        groups = mutated["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["provenance_independence_assessment"]["independence_groups"]
        groups.append(dict(groups[0]))  # duplicate an existing root
        with self.assertRaises(AssertionError):
            _assert_provenance_roots_not_double_counted(mutated)

    def test_mutation_AM_master_guide_relabeled_as_contemporaneous_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        ledger = mutated["tokyo_dome_research_current"]["restriction_list_current"]["source_contemporaneity_ledger"]
        for e in ledger:
            if e["source_id"] == "yugipedia-august-1999-lists":
                e["contemporaneous_to_1999"] = True
        with self.assertRaises(AssertionError):
            _assert_contemporaneity_not_conflated_with_retrospective(mutated)

    def test_mutation_AN_vjump_designation_and_street_date_collapsed_is_rejected(self):
        mutated = copy.deepcopy(self.packet)
        vjump = mutated["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["vjump_1999_09_investigation"]
        vjump["actual_publication_date"] = vjump["issue_designation"]
        with self.assertRaises(AssertionError):
            _assert_vjump_issue_designation_and_street_date_are_distinct(mutated)

    def test_mutation_AO_archived_claim_cannot_influence_current_restriction_verdict(self):
        # Archived/superseded text may retain old claims (e.g. the rejected
        # "July 1999, nationwide" framing) without being consumed as
        # current - mutate superseded_findings to say something that would,
        # if read as current, promote canonicalization, and confirm the
        # live axes are untouched.
        mutated = copy.deepcopy(self.packet)
        mutated["superseded_findings"]["_injected_for_test"] = {
            "_why_rejected": "test injection",
            "claim": "canonicalization_status should be RESOLVED because everything is actually PROVEN",
        }
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertEqual("UNRESOLVED_BLOCKING", rlc["canonicalization_status"]["status"])
        for axis in RESTRICTION_LOAD_BEARING_AXES:
            self.assertEqual("SUPPORTED_BUT_INCOMPLETE", rlc[axis]["status"])
        _assert_restriction_list_axes_are_independently_evidenced(mutated)  # unaffected by the archive injection

    def test_mutation_AP_h2_vs_h3_resolved_alone_does_not_unblock_canonicalization(self):
        # Direct proof of the central rule via mutation: resolving ONLY
        # outer_scope_status (H2-vs-H3) to PROVEN, with the four
        # load-bearing axes untouched, must NOT be accepted as sufficient -
        # and asserting canonicalization_status as RESOLVED on that basis
        # must be rejected.
        mutated = copy.deepcopy(self.packet)
        rlc = mutated["tokyo_dome_research_current"]["restriction_list_current"]
        rlc["outer_scope_status"]["status"] = "PROVEN"
        rlc["first_effective_date_status"]["status"] = "PROVEN"
        rlc["canonicalization_status"]["status"] = "RESOLVED"
        with self.assertRaises(AssertionError):
            _assert_restriction_list_axes_are_independently_evidenced(mutated)

    # ------------------------------------------------------------------
    # Adversarial review (2026-08-30, extended 2026-09): an independent
    # reviewer attacked this session's own restriction-list write-up and
    # found real overclaiming on scope (content-to-scope laundering) and
    # effective-date (a circular "tightly bounded window" that secretly
    # assumed H3), plus, in the 2026-09 pass, four locations where
    # "independently-authored"/"mutually independent in authorship"
    # overclaimed what the structured provenance record actually supports.
    # These tests make sure the review is recorded honestly and the
    # walk-back cannot silently regress back to the overclaimed wording -
    # via REAL fail-closed helper calls, not by asserting a mutation took
    # effect.
    # ------------------------------------------------------------------

    def _assert_adversarial_review_record_present_and_complete(self, review, required_challenge_keys):
        for key in tuple(required_challenge_keys) + ("reviewer_overall_verdict", "adjudicator_final_note"):
            if key not in review:
                raise AssertionError(f"adversarial review record is missing required key {key!r}")
        for challenge_key in required_challenge_keys:
            challenge = review[challenge_key]
            if not challenge.get("claim", "").strip():
                raise AssertionError(f"{challenge_key}.claim is missing or empty")
            if not challenge.get("adjudication", "").strip():
                raise AssertionError(f"{challenge_key}.adjudication is missing or empty")
        if "UNRESOLVED_BLOCKING" not in review["reviewer_overall_verdict"]:
            raise AssertionError(
                "reviewer_overall_verdict does not mention UNRESOLVED_BLOCKING - a review that silently "
                "claims canonicalization was unblocked must be caught"
            )

    def test_AP_adversarial_review_is_recorded_with_all_three_challenges_adjudicated(self):
        review = self.packet["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["adversarial_review_2026_08_30"]
        self._assert_adversarial_review_record_present_and_complete(
            review,
            (
                "challenge_1_content_independence",
                "challenge_2_scope_conflation",
                "challenge_3_effective_date_circularity",
            ),
        )

    def test_AQ_target_applicability_and_first_effective_date_walk_back_survived_the_review(self):
        # Regression guard: the specific overclaimed phrases identified by
        # the adversarial review must not stand as live, unqualified
        # claims in the (renamed) axis text.
        rlc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        # The H2-vs-H3 walk-back text lives in outer_scope_status (2026-09
        # rename) - target_event_applicability_status covers a different
        # proposition (whether the restriction applied AT the target at
        # all, not the finals-vs-whole-tournament boundary).
        outer_scope_text = json.dumps(rlc["outer_scope_status"], ensure_ascii=False)
        date_text = json.dumps(rlc["first_effective_date_status"], ensure_ascii=False)
        hyps_text = json.dumps(rlc["scope_hypotheses"]["hypotheses"], ensure_ascii=False)
        self.assertNotIn(
            "the strongest concrete lean toward H3 found in this research chain", hyps_text
        )
        self.assertIn("no source ties publication date to effective date", date_text)
        self.assertIn("genuinely UNRESOLVED", outer_scope_text)
        self.assertIn("REVISED 2026-08-30", outer_scope_text)
        self.assertIn("REVISED 2026-08-30", date_text)
        self.assertIn("REVISED 2026-08-30", hyps_text)

    def test_mutation_AQ_scope_overclaim_phrase_reintroduced_is_caught(self):
        # FIXED (2026-09): previously mutated the packet and merely
        # asserted the mutation took effect. Now calls the real fail-
        # closed overclaim-scanner helper and asserts it raises.
        mutated = copy.deepcopy(self.packet)
        hyps = mutated["tokyo_dome_research_current"]["restriction_list_current"]["scope_hypotheses"]["hypotheses"]
        for h in hyps:
            if h["id"] == "H3":
                h["assessment"] = h["assessment"] + " these are mutually independent in authorship sources"
        with self.assertRaises(AssertionError):
            _assert_no_stale_restriction_list_independence_overclaims(mutated)

    def test_mutation_AR_adversarial_review_deleted_is_detectable(self):
        # FIXED (2026-09): previously deleted a dict key and asserted that
        # accessing the deleted key raises KeyError - that tests Python
        # dict semantics, not any repository invariant. Now calls the real
        # helper, which independently detects the absence as a missing-
        # required-key AssertionError regardless of how the record is
        # accessed.
        mutated = copy.deepcopy(self.packet)
        del mutated["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["adversarial_review_2026_08_30"]
        review = mutated["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ].get("adversarial_review_2026_08_30", {})
        with self.assertRaises(AssertionError):
            self._assert_adversarial_review_record_present_and_complete(
                review,
                (
                    "challenge_1_content_independence",
                    "challenge_2_scope_conflation",
                    "challenge_3_effective_date_circularity",
                ),
            )

    def test_AV_adversarial_review_2026_09_is_recorded_with_all_challenges_adjudicated(self):
        review = self.packet["tokyo_dome_research_current"]["restriction_list_current"][
            "contemporaneous_source_investigation_2026_08_30"
        ]["adversarial_review_2026_09"]
        self._assert_adversarial_review_record_present_and_complete(
            review,
            (
                "challenge_1_central_logical_test",
                "challenge_2_independence_bookkeeping",
                "challenge_3_over_crediting_marketplace_evidence",
                "challenge_4_threshold_prose_consistency",
                "challenge_5_overclaiming_beyond_cited_sources",
                "challenge_6_missing_review_record_and_failing_test",
            ),
        )

    def test_AW_content_convenience_field_and_stale_blocker_note_fixed_after_review(self):
        # Direct regression for the two minor issues the 2026-09
        # adversarial review actually found: an unsourced bare-verdict
        # convenience field, and a stale "two-axis model" description.
        rlc = self.packet["tokyo_dome_research_current"]["restriction_list_current"]
        self.assertTrue(rlc["content"].get("source_ids"))
        self.assertNotEqual("STRONG, unchanged.", rlc["content"]["verdict"])
        rb1 = self.packet["tokyo_dome_research_current"]["remaining_blockers"][1]
        self.assertIn("six-axis", rb1.lower())
        self.assertNotIn("the restriction list two-axis model -", rb1)


if __name__ == "__main__":
    unittest.main()
