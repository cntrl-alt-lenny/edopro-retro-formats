"""Guards docs/state.md against re-accumulating volatile repository state.

docs/state.md is a *durable context* document: rulings, blockers, owner
preferences, and why things are parked. Live state (current SHA, whether a
brief is queued, branch/worktree layout, per-machine setup) must be
derived from git and docs/briefs/active.md instead.

This is enforced by a test rather than by discipline because discipline
already failed once: the file simultaneously claimed "Nothing queued yet"
and "Run the queued round-4 brief", and pinned a `main` SHA that a routine
Brain housekeeping commit had already invalidated -- within a single round.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "state.md"
BRIEFS = ROOT / "docs" / "briefs"
FRAMEWORK_DOCS = sorted((ROOT / "docs" / "agents").glob("*.md"))

# A full git object name. Deliberately 40 hex exactly: the Tokyo Dome
# certification digest is a 64-char sha256 historical anchor and the GOAT
# EDOPro content hash is 8 hex -- neither is volatile, and neither should
# trip this.
_GIT_SHA = re.compile(r"\b[0-9a-f]{40}\b")

# Phrases that assert live queue state, which docs/briefs/active.md owns.
_QUEUE_CLAIMS = (
    "nothing queued",
    "no brief queued",
    "nothing is queued",
    "no worker round in flight",
    "nothing in flight",
)


class StateDocIsDurableTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = STATE.read_text(encoding="utf-8")
        cls.lower = cls.text.lower()

    def test_pins_no_git_sha(self):
        """A stored commit SHA is stale the next time anyone commits --
        including when Brain commits its own housekeeping."""
        found = _GIT_SHA.findall(self.text)
        self.assertEqual(
            [],
            found,
            "docs/state.md must not pin a git SHA; derive it with "
            f"`git rev-parse`. Found: {found}",
        )

    def test_makes_no_live_queue_claim(self):
        """Whether a brief is queued is owned by docs/briefs/active.md,
        which states its own Status:. Duplicating it desynced once."""
        for phrase in _QUEUE_CLAIMS:
            with self.subTest(phrase=phrase):
                self.assertNotIn(
                    phrase,
                    self.lower,
                    f"docs/state.md claims queue state ({phrase!r}); that "
                    "belongs to docs/briefs/active.md",
                )

    def test_directs_readers_to_derive_live_state(self):
        """The file must say where live state actually comes from, so a
        fresh Brain session doesn't reach for a stored value."""
        for marker in ("git status", "active.md", "core.hooksPath"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.text)

    def test_does_not_record_per_machine_setup_status(self):
        """Per-machine facts (which laptop has the hook configured) are
        not shareable repository state."""
        for phrase in ("windows machine", "on the mac as of", "macbook as of"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.lower)

    def test_active_brief_states_its_own_status(self):
        """The contract the above depends on: active.md is self-describing,
        so nothing else needs to mirror it."""
        active = BRIEFS / "active.md"
        self.assertTrue(active.is_file(), "docs/briefs/active.md is missing")
        head = active.read_text(encoding="utf-8")[:400].lower()
        self.assertIn("status:", head)


class FrameworkDocsAreDurableTest(unittest.TestCase):
    """Keep framework guidance host-independent and derivable."""

    def test_framework_docs_do_not_pin_git_shas(self):
        for document in FRAMEWORK_DOCS:
            with self.subTest(document=document.name):
                found = _GIT_SHA.findall(document.read_text(encoding="utf-8"))
                self.assertEqual([], found, f"{document} pins a git SHA: {found}")

    def test_framework_docs_do_not_pin_machine_setup(self):
        volatile_phrases = (
            "windows machine",
            "on the mac as of",
            "macbook as of",
            "currently a windows",
            "m1 macbook",
        )
        for document in FRAMEWORK_DOCS:
            lower = document.read_text(encoding="utf-8").lower()
            for phrase in volatile_phrases:
                with self.subTest(document=document.name, phrase=phrase):
                    self.assertNotIn(phrase, lower)


if __name__ == "__main__":
    unittest.main()
