"""Deck-level legality checking against a canonical format's shipped whitelist.

Legality is never reimplemented here: `check_deck` calls `lflist.build_lflist()`
— the exact function that produces `dist/lflists/*.lflist.conf` — and checks a
parsed `.ydk` deck against its `entries` (the same {passcode: allowed count}
map the shipped list encodes). A checker that disagreed with the artifact
would be worse than no checker (see docs/briefs/archive for round 8's brief);
this one cannot disagree with it by construction.

`.ydk` parsing mirrors EDOPro's real `LoadCardList`
(`gframe/deck_manager.cpp:272-300`, `edo9300/edopro` @ `9d6fb3e8417c88`, the
pinned `edopro-source` revision in `data/sources.json` — fetched and read
directly for this round, not assumed):

- a line that is EXACTLY `"#extra"` switches subsequent lines to the extra
  deck; any OTHER line starting with `#` (including `#main`, `#created by
  ...`) is a pure comment and never contributes a passcode. There is no
  special handling of `"#main"` at all — lines before any marker default to
  the main deck.
- ANY line starting with `!` switches to the side deck for the rest of the
  file, regardless of what follows the `!` — real files always write
  `!side` by convention, but the client's parser does not check the text.
- a line containing a leading run of digits (optionally preceded by
  whitespace) is parsed for that leading numeric passcode, mirroring
  `std::stoul`'s leading-prefix parse — trailing non-digit text after the
  number does not invalidate the line, but a line that does not START with
  (whitespace then) a digit is silently skipped, exactly as the client does.

Deck-content checking mirrors `DeckManager::CheckCards`
(`docs/research/edopro-lflists.md` §6.2, citing `deck_manager.cpp:192-200`):
counting merges every card under its alias root (`alias if alias else code`)
across main+extra+side combined in ONE shared counter, but the *limit*
lookup for a specific printed code tries that code's own entry first, then
its alias — and on a whitelist (all three formats here are whitelists) the
alias fallback for the limit lookup only applies within the +/-10 artwork
range (`ARTWORK_OFFSET`), never for a functional alias (a pre-errata
`511xxxxxx` code, or GOAT's `504700xxx` reference-parity codes) — those must
resolve to a whitelist entry under their own code.

Unlike the real client, which returns on the FIRST violation found
(`deck_manager.cpp:192-200`'s `return LFLIST`/`return CARDCOUNT`), this
checker reports every distinct violation in one pass — more useful for a
human debugging a decklist than a single early exit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .lflist import ARTWORK_OFFSET, build_lflist, historical_identity, select_applicable_errata
from .model import CardIndex, Format
from .repo import Repository

_LEADING_NUMBER = re.compile(r"\s*(\d+)")


@dataclass(frozen=True)
class ParsedDeck:
    main: tuple[int, ...]
    extra: tuple[int, ...]
    side: tuple[int, ...]

    @property
    def all_codes(self) -> tuple[int, ...]:
        return (*self.main, *self.extra, *self.side)


def parse_ydk(text: str) -> ParsedDeck:
    """See module docstring for the exact, source-cited parsing rules."""
    main: list[int] = []
    extra: list[int] = []
    side: list[int] = []
    is_extra = False
    is_side = False
    for line in text.splitlines():
        if not line:
            continue
        if line[0] == "#":
            if line == "#extra":
                is_extra = True
            continue
        if line[0] == "!":
            is_side = True
            continue
        match = _LEADING_NUMBER.match(line)
        if not match:
            continue
        code = int(match.group(1))
        if is_side:
            side.append(code)
        elif is_extra:
            extra.append(code)
        else:
            main.append(code)
    return ParsedDeck(main=tuple(main), extra=tuple(extra), side=tuple(side))


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


# formats/*/format.json's client.forbidden_card_types (TYPE_XYZ / TYPE_PENDULUM
# / TYPE_LINK) has no data behind it: data/cards/index.json carries only
# passcode/name/alias_of/ot, never a card type (see the brief and Non-goals —
# extending the index is a DATA/SCHEMA decision, not this round's). Round 8
# investigated whether the check is nonetheless redundant for these three
# formats and found it IS: every forbidden type's real first TCG printing
# postdates every one of the three formats' own release-cutoff dates, so a
# release-cutoff-derived pool cannot contain one regardless —
#   - Xyz Monsters: earliest TCG printing "Starter Deck: Dawn of the Xyz"
#     (YS11), 2011-07-12 (data/releases/products/starter-deck-dawn-of-the-xyz.json)
#     and Generation Force (GENF), 2011-08-16/08-12
#     (data/releases/products/generation-force.json) — both AFTER GOAT's
#     2005-04-01 and Edison's 2010-05-10 cutoffs (where Xyz is forbidden),
#     and correctly BEFORE Tengu's 2011-09-17 cutoff (where Xyz is legal —
#     Tengu's own pool notes cite GENF and "early Xyz monsters").
#   - Pendulum/Link Monsters: real-world TCG introduction is 2014/2017
#     respectively, both far after Tengu's 2011-09-17 cutoff — the latest of
#     the three — and data/releases/coverage.json's own TCG window ends at
#     that same date, so no product dated after it exists in this project's
#     release data for ANY of the three pools to draw from.
# The pool-membership check below already excludes anything not in the
# whitelist, so this structural argument (not a card-type inspection) is
# what makes the type check redundant here — it does not generalise to a
# hypothetical future format whose cutoff postdates one of these dates.
FORBIDDEN_TYPE_NOTE = (
    "not checked: forbidden_card_types (Xyz/Pendulum/Link) has no data behind "
    "it (data/cards/index.json carries no card type) but is redundant for "
    "this format — its release-cutoff pool cannot contain a card of any type "
    "it forbids, since every such type's real first TCG printing postdates "
    "this format's own cutoff. See retroformats/deckcheck.py's FORBIDDEN_TYPE_NOTE "
    "comment for the exact dates and citations."
)


@dataclass
class DeckCheckResult:
    format_id: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def legal(self) -> bool:
        return not self.findings


def _limit_for(code: int, entries: dict[int, int], card_index: CardIndex) -> int | None:
    """`LFList::GetLimitationIterator` (deck_manager.h:23-30): own code first,
    then alias — but on a whitelist (every format here is one) the alias
    fallback only applies within the +/-10 artwork range; a functional alias
    (pre-errata/GOAT-variant identity) must be listed under its own code."""
    if code in entries:
        return entries[code]
    alias = card_index.alias_of(code)
    if alias is not None and abs(code - alias) < ARTWORK_OFFSET and alias in entries:
        return entries[alias]
    return None


def _count_key(code: int, card_index: CardIndex) -> int:
    """`uint32_t code = cit->alias ? cit->alias : cit->code;` — counting
    always merges under the alias root, unconditionally (no artwork-range
    restriction; that restriction is limit-lookup-only, see `_limit_for`)."""
    alias = card_index.alias_of(code)
    return alias if alias is not None else code


def _card_label(code: int, card_index: CardIndex) -> str:
    name = card_index.name_of(code)
    return f"{code} ({name})" if name else str(code)


def check_deck(deck: ParsedDeck, fmt: Format, repo: Repository) -> DeckCheckResult:
    """Check `deck` against `fmt`'s shipped whitelist and rule-profile deck
    sizes. Legality comes from `build_lflist(fmt, repo).entries` — the same
    call `retroformats build` makes — never a parallel computation."""
    findings: list[Finding] = []
    entries = build_lflist(fmt, repo).entries
    card_index = repo.card_index
    rule_profile = repo.rule_profiles[fmt.rule_profile_id]
    client = (rule_profile.raw or {}).get("client", {}) or {}

    for section_name, codes, key in (
        ("main", deck.main, "main_deck"),
        ("extra", deck.extra, "extra_deck"),
        ("side", deck.side, "side_deck"),
    ):
        bounds = client.get(key)
        if not bounds:
            continue
        lo, hi = bounds
        count = len(codes)
        if not (lo <= count <= hi):
            findings.append(
                Finding(
                    "deck.bad-size",
                    f"{section_name} deck has {count} cards; {rule_profile.id} requires {lo}-{hi}",
                )
            )

    overrides = select_applicable_errata(fmt, repo)
    ccount: dict[int, int] = {}
    for code in deck.all_codes:
        key = _count_key(code, card_index)
        ccount[key] = ccount.get(key, 0) + 1

    for code in sorted(set(deck.all_codes)):
        limit = _limit_for(code, entries, card_index)
        label = _card_label(code, card_index)
        if limit is None:
            override = overrides.get(code)
            if override is not None:
                historical_passcode, _variants = historical_identity(override.implementation)
                findings.append(
                    Finding(
                        "deck.substituted-card",
                        f"{label}: not legal in {fmt.id} — this card is substituted in this "
                        f"format because its modern implementation would behave incorrectly "
                        f"for the era (erratum {override.erratum.id}); the legal identity is "
                        f"{_card_label(historical_passcode, card_index)}",
                    )
                )
                continue
            alias = card_index.alias_of(code)
            alias_limit = _limit_for(alias, entries, card_index) if alias is not None else None
            if alias is not None and alias_limit is not None:
                findings.append(
                    Finding(
                        "deck.wrong-historical-identity",
                        f"{label}: not legal in {fmt.id} — this is a historical/variant "
                        f"identity of {_card_label(alias, card_index)}, which IS legal here; "
                        f"this format does not substitute it, so play the modern identity "
                        f"instead",
                    )
                )
                continue
            findings.append(
                Finding("deck.illegal-card", f"{label}: not legal in {fmt.id} (not on the pool whitelist)")
            )
            continue
        key = _count_key(code, card_index)
        count = ccount[key]
        if count > limit:
            findings.append(
                Finding(
                    "deck.overcount",
                    f"{label}: {count} copies in the deck (main+extra+side combined), "
                    f"but only {limit} allowed in {fmt.id}",
                )
            )

    return DeckCheckResult(format_id=fmt.id, findings=findings)
