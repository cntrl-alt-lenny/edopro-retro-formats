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
