"""Shared fixtures: an in-memory miniature repository for unit tests."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TempRepoTest(unittest.TestCase):
    """A test case with a scratch canonical-data tree it can mutate freely."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="retroformats-test-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        for sub in (
            "formats",
            "data/banlists/tcg",
            "data/pools",
            "data/rule-profiles",
            "data/errata",
            "data/cards",
            "data/releases",
        ):
            (self.root / sub).mkdir(parents=True)
        self.write(
            "data/sources.json",
            {
                "sources": [
                    {"id": "test-source", "kind": "other", "title": "Test source", "url": "https://example.invalid"}
                ]
            },
        )

    def write(self, rel: str, payload) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    # -- canned records --------------------------------------------------

    def add_card_index(self, cards):
        self.write(
            "data/cards/index.json",
            {
                "generated_by": "test",
                "source": {"repository": "test", "revision": "0"},
                "cards": cards,
            },
        )

    def add_banlist(self, id="tcg-2005-04", entries=(), **kw):
        payload = {
            "id": id,
            "region": "TCG",
            "effective_date": "2005-04-01",
            "entries": list(entries),
            "sources": ["test-source"],
        }
        payload.update(kw)
        region, rest = id.split("-", 1)
        self.write(f"data/banlists/{region}/{rest}.json", payload)
        return payload

    def add_pool(self, id="pool-test", cards=(), **kw):
        payload = {
            "id": id,
            "region": "TCG",
            "kind": "extensional",
            "cards": list(cards),
            "sources": ["test-source"],
            "legality_basis": "availability",
        }
        payload.update(kw)
        self.write(f"data/pools/{id.removeprefix('pool-')}.json", payload)
        return payload

    def add_rule_profile(self, id="rules-test", **kw):
        payload = {
            "id": id,
            "name": "Test rules",
            "engine": {"preset": None, "flags": ["DUEL_1ST_TURN_DRAW"]},
            "sources": ["test-source"],
        }
        payload.update(kw)
        self.write(f"data/rule-profiles/{id.removeprefix('rules-')}.json", payload)
        return payload

    def add_format(
        self,
        id="2005-04-test",
        banlist="tcg-2005-04",
        pool="pool-test",
        rules="rules-test",
        **kw,
    ):
        payload = {
            "id": id,
            "name": "Test Format",
            "region": "TCG",
            "period": {"start": "2005-04-01", "end": None, "snapshot": "2005-04-01"},
            "banlist": banlist,
            "card_pool": pool,
            "rule_profile": rules,
            "implementation_status": {
                "banlist": "partial",
                "card_pool": "partial",
                "rule_profile": "partial",
                "errata": "partial",
                "overall": "partial",
            },
            "sources": ["test-source"],
        }
        payload.update(kw)
        self.write(f"formats/{id}/format.json", payload)
        return payload


    def add_erratum(
        self,
        id="erratum-beta",
        modern=None,
        classification="functional",
        changes=None,
        impl=None,
        review="reviewed",
        **kw,
    ):
        payload = {
            "id": id,
            "modern_card": modern or {"passcode": 200, "name": "Beta"},
            "classification": classification,
            "changes": changes if changes is not None else [change()],
            "implementation": impl
            or {"strategy": "reuse-upstream", "historical_passcode": 510000000, "status": "complete"},
            "review": {"status": review},
            "sources": ["test-source"],
        }
        payload.update(kw)
        self.write(f"data/errata/{id.removeprefix('erratum-')}.json", payload)
        return payload

    def add_erratum_v2(
        self,
        id="erratum-v2-beta",
        modern=None,
        classification="ruling",
        events=None,
        ordering=None,
        states=None,
        review="reviewed",
        **kw,
    ):
        payload = {
            "id": id,
            "modern_card": modern or {"passcode": 200, "name": "Beta"},
            "classification": classification,
            "events": events if events is not None else {"e1": v2_event()},
            "ordering": ordering if ordering is not None else {},
            "review": {"status": review},
            "sources": ["test-source"],
        }
        if states is not None:
            payload["states"] = states
        payload.update(kw)
        self.write(f"data/errata/{id.removeprefix('erratum-')}.json", payload)
        return payload

    def add_product(self, code="SET1", printings=(), release_events=None, **kw):
        payload = {
            "id": code.lower(),
            "code": code,
            "name": f"Test Product {code}",
            "kind": "booster",
            "release_events": (
                release_events
                if release_events is not None
                else [event("tcg-na", "2005-01-01")]
            ),
            "printings": list(printings),
            "sources": ["test-source"],
        }
        payload.update(kw)
        self.write(f"data/releases/products/{payload['id']}.json", payload)
        return payload

    def add_coverage(self, windows=None, **kw):
        payload = {
            "windows": windows
            if windows is not None
            else [
                {
                    "territories": ["tcg"],
                    "from": "2002-01-01",
                    "through": "2010-12-31",
                    "status": "complete",
                }
            ],
            "sources": ["test-source"],
        }
        payload.update(kw)
        self.write("data/releases/coverage.json", payload)
        return payload

    def add_gaps(self, *gaps):
        self.write(
            "data/releases/gaps.json",
            {"gaps": list(gaps), "sources": ["test-source"]},
        )

    def add_import_report(self, **kw):
        # stats default to the products currently on disk so the validator's
        # report-staleness binding passes; call AFTER add_product().
        import json as _json

        generated = curated = 0
        products_dir = self.root / "data" / "releases" / "products"
        if products_dir.is_dir():
            for path in products_dir.glob("*.json"):
                if _json.loads(path.read_text()).get("curated"):
                    curated += 1
                else:
                    generated += 1
        payload = {
            "importer": "test",
            "stats": {"products_written": generated, "curated_preserved": curated},
            "yugipedia_only_products": [],
            "products_without_printings": [],
            "curated_covered_products": [],
            "unmatched_cards": [],
        }
        payload.update(kw)
        self.write("data/imported/releases-report.json", payload)
        return payload

    def add_cutoff_pool(self, id="pool-cut", cutoff_date="2005-06-01", cards=None, **cutoff_kw):
        payload = {
            "id": id,
            "region": "TCG",
            "kind": "release-cutoff",
            "cutoff": {"cutoff_date": cutoff_date, **cutoff_kw},
            "sources": ["test-source"],
            "legality_basis": "availability",
        }
        if cards is not None:
            payload["cards"] = cards
        self.write(f"data/pools/{id.removeprefix('pool-')}.json", payload)
        return payload


def card(passcode: int, name: str, **kw):
    ref = {"passcode": passcode, "name": name}
    ref.update(kw)
    return ref


def change(kind="functional", date=None, summary="changed", **kw):
    """An erratum change entry in the evolved shape. Effective-chronology
    fields (precision, status, old_attested_through, new_attested_from, basis)
    are passed via effective_* keywords."""
    effective = {"date": date}
    for key in ("precision", "status", "old_attested_through", "new_attested_from", "basis"):
        if f"effective_{key}" in kw:
            effective[key] = kw.pop(f"effective_{key}")
    entry = {"kind": kind, "effective": effective, "summary": summary, "sources": ["test-source"]}
    entry.update(kw)
    return entry


def v2_transition(kind="ruling", summary="changed", axis=None, **kw):
    t = {"kind": kind, "summary": summary, "sources": ["test-source"]}
    if axis is not None:
        t["axis"] = axis
    t.update(kw)
    return t


def v2_event(effective=None, transitions=None, cooccurrence_sources=None, **kw):
    """One events{} entry for the v2 historical-event DAG. Effective
    defaults to completely undated (permanently AMBIGUOUS) — pass an
    explicit `effective` dict to pin a chronology."""
    e = {
        "effective": effective if effective is not None else {"date": None},
        "transitions": transitions if transitions is not None else [v2_transition()],
    }
    if cooccurrence_sources is not None:
        e["cooccurrence_sources"] = cooccurrence_sources
    e.update(kw)
    return e


def v2_coverage(kind="reuse-upstream", **kw):
    c = {"kind": kind}
    if kind == "reuse-upstream":
        c.setdefault("historical_passcode", 511000000)
        c.setdefault("upstream", "ProjectIgnis/BabelCDB goat-entries.cdb")
    elif kind == "custom-script":
        c.setdefault("historical_passcode", 511000001)
        c.setdefault("script", "dist/scripts/c511000001.lua")
    elif kind == "known-gap":
        c.setdefault("gap_reason", "no upstream implementation exists")
        c.setdefault("gap_sources", ["test-source"])
    c.update(kw)
    return c


def implementation(strategy="reuse-upstream", historical_passcode=None, status="complete", **kw):
    impl = {"strategy": strategy, "status": status}
    if historical_passcode is not None:
        impl["historical_passcode"] = historical_passcode
    impl.update(kw)
    return impl


def event(territory: str, date: str, **kw):
    ev = {"territory": territory, "date": date, "sources": ["test-source"]}
    ev.update(kw)
    return ev


def printing(passcode: int, name: str, number: str | None = None, **kw):
    row = {"passcode": passcode, "name": name}
    if number:
        row["numbers"] = [number]
    row.update(kw)
    return row


def gap(id="gap-test", **kw):
    record = {
        "id": id,
        "kind": "missing-product-printings",
        "subjects": ["Test Missing Product"],
        "territories": ["tcg-na"],
        "possible_from": "2005-03-01",
        "status": "unresolved",
        "impact": "pool-membership",
        "sources": ["test-source"],
    }
    record.update(kw)
    return record


# Round 031 (roadmap item 7): the six generated cards whose historical state applies at BOTH
# the Edison (2010-04-24) and the Tengu (2011-09-17) snapshot, so both lists name them.
# {erratum id: (modern passcode, generated passcode)}.
ROUND_031_GENERATED = {
    "erratum-goddess-of-whim": (67959180, 600000004),
    "erratum-strike-ninja": (41006930, 600000005),
    "erratum-green-baboon-defender-of-the-forest": (46668237, 600000006),
    "erratum-rise-of-the-snake-deity": (16067089, 600000007),
    "erratum-malefic-blue-eyes-white-dragon": (9433350, 600000008),
    "erratum-soul-rope": (37383714, 600000009),
}
ROUND_031_PASSCODES = frozenset(generated for _modern, generated in ROUND_031_GENERATED.values())

# Round 035: cards whose generated version was removed because Konami's period rulings show
# the modern card behaves as the era card did (docs/research/period-rulings-generated-scripts.md).
# {erratum id: (modern passcode, retired generated passcode)}. The lists use the modern code
# again; swap_retired_forward() reconstructs what they held before, so every pin taken then
# can still be asserted.
ROUND_035_RETIRED = {
    "erratum-metalzoa": (50705071, 600000001),
    "erratum-rise-of-the-snake-deity": (16067089, 600000007),
    "erratum-malefic-blue-eyes-white-dragon": (9433350, 600000008),
    "erratum-soul-rope": (37383714, 600000009),
}
# The three of them whose erratum record had to become a full v2 record: the single-event
# sugar cannot carry a cosmetic transition (model._desugar_v2_sugar). Before round 035 the
# corpus was 180 sugar records and 116 full v2 records; it is now 177 and 119.
ROUND_035_CONVERTED_TO_FULL_V2 = frozenset(
    {"erratum-metalzoa", "erratum-malefic-blue-eyes-white-dragon", "erratum-rise-of-the-snake-deity"}
)
ROUND_035_RETIRED_PASSCODES = frozenset(generated for _modern, generated in ROUND_035_RETIRED.values())
# The round-031 cards that are still generated and whose state applies at Tengu's snapshot.
TENGU_GENERATED_PASSCODES = ROUND_031_PASSCODES - ROUND_035_RETIRED_PASSCODES
# The removed cards whose generated code Tengu's list carried before round 035 (Metalzoa's
# never was: its erratum, 2011-08-13, precedes Tengu's snapshot).
ROUND_035_RETIRED_AT_TENGU_PASSCODES = ROUND_035_RETIRED_PASSCODES - {600000001}
# Every number in the reserved range that was assigned or held for a generated card and is not
# generated now. None is ever assigned again: 600000003 (Night Assailant, held back on thin
# evidence, round 029), the four above, and 600000010-600000017 (round 034's eight cards, which
# period rulings did not support; that round was never merged).
#
# Round 036 changes that set: 600000016 is generated again (Dice Re-Roll) and 600000018-21 are
# assigned; 600000004 and 600000006 are retired with the cards above; 600000010-15 (the five
# strict-nomi cards and Dark Master - Zorc: the modern card is right) and 600000017 (Second Coin
# Toss: no third behaviour is established) stay retired.
RETIRED_PASSCODES = frozenset(
    {600000003, 600000004, 600000006}
    | ROUND_035_RETIRED_PASSCODES
    | set(range(600000010, 600000016))
    | {600000017}
)


def swap_generated_back(entries, custom_cards, passcodes=None):
    """A built lflist's {code: count} with each generated card's code replaced by
    the modern card it aliases (only `passcodes` if given). The result is what
    the list held before those cards were generated, so a pin taken then can
    still be asserted against it."""
    out = dict(entries)
    for card in custom_cards.values():
        if (passcodes is None or card.passcode in passcodes) and card.passcode in out:
            out[card.alias] = out.pop(card.passcode)
    return out


def swap_retired_forward(entries, passcodes=None):
    """A built lflist's {code: count} with each round-035 card's modern code replaced by
    the generated code it had before the card was removed (only `passcodes` if given), so
    a hash taken before round 035 can still be asserted against a list built now. Only
    codes the list holds are swapped: a list that never carried the generated card (Tengu
    never carried Metalzoa's) is left alone."""
    out = dict(entries)
    for modern, generated in ROUND_035_RETIRED.values():
        if (passcodes is None or generated in passcodes) and modern in out:
            out[generated] = out.pop(modern)
    return out


# Every generated card any round ever put in a list: {generated passcode: the modern card it
# aliases}. Rounds 029-030 (Metalzoa, Super Vehicroid - Stealth Union) and 031 (the six
# above), including the four round 035 removed. swap_back() undoes them, so a hash pinned
# at any earlier round can still be asserted against today's list.
ALL_GENERATED_ALIASES = {
    600000001: 50705071,
    600000002: 3897065,
    **{generated: modern for modern, generated in ROUND_031_GENERATED.values()},
}
# The round-031 substitutions still in force at Tengu's snapshot after round 035 ({erratum id: (modern, generated)}).
TENGU_GENERATED_AFTER_ROUND_035 = {k: v for k, v in ROUND_031_GENERATED.items() if k not in ROUND_035_RETIRED}

# Round 036: the owner decided on 2026-09-29 that UDE-era card rulings count at Edison and Tengu
# unless a later Konami document replaced them. Two more generated cards are removed because a
# ruling shows the modern card behaves as the era card did (Goddess of Whim: the card FAQ says
# once per turn; Green Baboon: the Damage Step by Konami's lists and the face-up requirement by
# the Netrep answer and the card FAQ), and five are added because a ruling supports the
# difference: Dice Re-Roll (round 034's script, reworked), Machina Peacekeeper and Machina
# Gearframe (the Union Condition), Elemental HERO Chaos Neos (either Main Phase) and Treeborn
# Frog (no use limit). {erratum id: (modern passcode, generated passcode)}; every one applies at both
# snapshots. to_round_035() reconstructs the list as round 035 left it, so every pin taken then
# can still be asserted against a list built now.
ROUND_036_RETIRED = {
    "erratum-goddess-of-whim": (67959180, 600000004),
    "erratum-green-baboon-defender-of-the-forest": (46668237, 600000006),
}
ROUND_036_ADDED = {
    "erratum-dice-re-roll": (83241722, 600000016),
    "erratum-machina-peacekeeper": (78349103, 600000018),
    "erratum-machina-gearframe": (42940404, 600000019),
    "erratum-elemental-hero-chaos-neos": (17032740, 600000020),
    "erratum-treeborn-frog": (12538374, 600000021),
}
ROUND_036_RETIRED_PASSCODES = frozenset(generated for _modern, generated in ROUND_036_RETIRED.values())
ROUND_036_ADDED_PASSCODES = frozenset(generated for _modern, generated in ROUND_036_ADDED.values())
# The three round-036 records that had to become full v2 records (the single-event sugar cannot carry a
# cosmetic transition): before round 036 the corpus was 177 sugar and 119 full v2 records, now 174 and 122.
ROUND_036_CONVERTED_TO_FULL_V2 = frozenset(
    {"erratum-goddess-of-whim", "erratum-green-baboon-defender-of-the-forest", "erratum-vw-tiger-catapult"}
)
# Both conversions: before round 035 the corpus was 116 full v2 and 180 sugar records.
CONVERTED_TO_FULL_V2 = ROUND_035_CONVERTED_TO_FULL_V2 | ROUND_036_CONVERTED_TO_FULL_V2
# The round-031 substitutions still in force at Tengu's snapshot ({erratum id: (modern, generated)}).
TENGU_GENERATED = {
    **{k: v for k, v in TENGU_GENERATED_AFTER_ROUND_035.items() if k not in ROUND_036_RETIRED},
    **ROUND_036_ADDED,
}
TENGU_GENERATED_PASSCODES_NOW = frozenset(generated for _modern, generated in TENGU_GENERATED.values())
# swap_back() also undoes the cards round 036 added.
ALL_GENERATED_ALIASES.update({generated: modern for modern, generated in ROUND_036_ADDED.values()})


# Round 037 (docs/research/text-only-errata-audit.md): period rulings show two more records' modern card
# behaves as the era card did, so Edison's and Tengu's lists use the modern code again instead of Ignis's
# pre-errata variant. {modern passcode: the variant's passcode before round 037}.
ROUND_037_TO_MODERN = {
    9995766: 9995776,  # Imperial Custom
    63394872: 63394882,  # Senet Switch
}
# The four records that had to become full v2 records in round 037: the single-event sugar cannot carry a
# cosmetic transition, nor two transitions in one event (Gaia Soul, Imperial Custom and Senet Switch
# became cosmetic; D.D. Survivor gained a second transition). The corpus was 174 sugar and 122 full v2
# records before round 037, and is now 170 and 126.
ROUND_037_CONVERTED_TO_FULL_V2 = frozenset(
    {
        "erratum-gaia-soul-the-combustible-collective",
        "erratum-imperial-custom",
        "erratum-senet-switch",
        "erratum-d-d-survivor",
    }
)
ROUND_037_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "round-037-before"
# All three rounds' conversions: before round 035 the corpus was 116 full v2 and 180 sugar records.
CONVERTED_TO_FULL_V2 = CONVERTED_TO_FULL_V2 | ROUND_037_CONVERTED_TO_FULL_V2


# The two of round 037's cosmetic records that used an Ignis variant (erratum ids).
ROUND_037_COSMETIC_RECORDS = frozenset({"erratum-imperial-custom", "erratum-senet-switch"})


def to_round_036(entries):
    """A built lflist's {code: count} as round 036 left it: each record round 037 made cosmetic that
    used an Ignis variant holds that variant again instead of the modern card."""
    out = dict(entries)
    for modern, variant in ROUND_037_TO_MODERN.items():
        if modern in out:
            out[variant] = out.pop(modern)
    return out


def record_before_round_037(path):
    """The bytes of a data/errata record as it stood on main before round 037 when round 037 edited it
    (tests/fixtures/round-037-before/), else its bytes now. For the frozen migration tests, whose pins
    were taken on the earlier record."""
    fixture = ROUND_037_FIXTURES / Path(path).name
    return (fixture if fixture.is_file() else Path(path)).read_bytes()


def to_round_035(entries):
    """A built lflist's {code: count} as round 035 left it: each card round 036 added is its modern
    card again, and each card round 036 removed is its generated code again."""
    entries = to_round_036(entries)
    out = dict(entries)
    for modern, generated in ROUND_036_ADDED.values():
        if generated in out:
            out[modern] = out.pop(generated)
    for modern, generated in ROUND_036_RETIRED.values():
        if modern in out:
            out[generated] = out.pop(modern)
    return out


def swap_back(entries, passcodes=None):
    """A built lflist's {code: count} with each generated code (only `passcodes` if given)
    replaced by the modern card it aliases, from the static ALL_GENERATED_ALIASES map, so
    it also undoes a card that no longer exists in data/custom-cards/."""
    out = dict(entries)
    for generated, modern in ALL_GENERATED_ALIASES.items():
        if (passcodes is None or generated in passcodes) and generated in out:
            out[modern] = out.pop(generated)
    return out



# Round 037: the frozen pre-migration corpora that the migration harnesses re-materialise and validate
# predate the rulings gate on errata records (`erratum.rulings-check-missing`), which asks for a check
# no frozen record carries. The harnesses keep asserting that they add no OTHER error; the live
# repository, which does carry the checks, is held to the gate by tests/test_errata_rulings_gate.py.
FROZEN_CORPUS_EXEMPT_CODES = frozenset({"erratum.rulings-check-missing"})


def errors_without_the_frozen_exemption(validator):
    """A validator's errors, less the rulings-gate code the frozen migration corpora cannot carry."""
    return [f for f in validator.errors if f.code not in FROZEN_CORPUS_EXEMPT_CODES]
