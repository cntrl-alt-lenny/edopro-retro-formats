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
