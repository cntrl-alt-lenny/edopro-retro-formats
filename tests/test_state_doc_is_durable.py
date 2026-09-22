"""Guards docs/state.md against re-accumulating one specific kind of volatile
repository state: a claim about whether a round is currently queued.

docs/state.md is a *durable context* document: rulings, blockers, owner
preferences, and why things are parked. Whether a round is queued or in
flight is owned by `fw.py status` and `docs/rounds/`, derived from git, never
duplicated in prose here.

This is enforced by a test rather than by discipline because discipline
already failed once: the file simultaneously claimed "Nothing queued yet"
and "Run the queued round-4 brief", and pinned a `main` SHA that a routine
Brain housekeeping commit had already invalidated -- within a single round.

The rest of what this file used to check (no stored git SHA outside
'## Historical anchors', no personal paths or per-machine setup facts, the
same for every document under docs/agents/) is now `tests/test_framework.py`
via `fw.py check`'s `check_project`, which covers every tracked document
agents read (AGENTS.md, CLAUDE.md, docs/state.md, docs/agents/**, docs/rounds/**),
not only docs/state.md -- see docs/agents/FRAMEWORK.md and tools/fw.py's
`check_project`. Duplicating that here would be a second, driftable copy of
the same check.
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "state.md"

# Phrases that assert live queue state, which fw.py status and docs/rounds/
# own instead.
_QUEUE_CLAIMS = (
    "nothing queued",
    "no brief queued",
    "nothing is queued",
    "no worker round in flight",
    "no builder round in flight",
    "nothing in flight",
)


class StateDocIsDurableTest(unittest.TestCase):
    def test_makes_no_live_queue_claim(self):
        """Whether a round is queued or in flight is owned by `fw.py status`
        and `docs/rounds/`. Duplicating it in prose desynced once."""
        lower = STATE.read_text(encoding="utf-8").lower()
        for phrase in _QUEUE_CLAIMS:
            with self.subTest(phrase=phrase):
                self.assertNotIn(
                    phrase,
                    lower,
                    f"docs/state.md claims queue state ({phrase!r}); that "
                    "belongs to `fw.py status` and docs/rounds/",
                )


if __name__ == "__main__":
    unittest.main()
