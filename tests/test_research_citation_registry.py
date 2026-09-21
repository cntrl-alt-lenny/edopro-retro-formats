"""Tests for the research citation registry ratchet."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .research_citation_registry import BACKLOG_RELATIVE, REDIRECT_EXEMPTION_MARKER, check, report


def _write_fixture(root: Path, research: str, sources: list[dict], backlog: list[str]) -> Path:
    (root / "docs/research").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "tests/fixtures").mkdir(parents=True)
    (root / "docs/research/example.md").write_text(research)
    (root / "data/sources.json").write_text(json.dumps({"sources": sources}))
    backlog_path = root / BACKLOG_RELATIVE
    backlog_path.write_text(json.dumps({"entries": [{"url": url} for url in backlog]}))
    return backlog_path


class ResearchCitationRegistryTest(unittest.TestCase):
    def test_current_tree_passes(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual([], check(root))

    def test_planted_unregistered_citation_fails(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            backlog = _write_fixture(
                root,
                "See https://example.test/unregistered for the source.\n",
                [],
                [],
            )
            errors = check(root, backlog)
            self.assertTrue(any("not listed in backlog" in error for error in errors), errors)

    def test_grown_backlog_fails(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            backlog = _write_fixture(root, "No external citation here.\n", [], ["https://example.test/grown"])
            errors = check(root, backlog)
            self.assertTrue(any("backlog entry is no longer" in error for error in errors), errors)

    def test_registered_and_removed_backlog_entry_passes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            url = "https://example.test/registered"
            backlog = _write_fixture(root, f"See {url}.\n", [], [url])
            # The original state is a valid baseline backlog for this isolated
            # demonstration; after registration the entry may be removed.
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset(registry._url_keys(url))
                self.assertEqual([], check(root, backlog))
                (root / "data/sources.json").write_text(json.dumps({"sources": [{"id": "registered", "url": url}]}))
                backlog.write_text(json.dumps({"entries": []}))
                self.assertEqual([], check(root, backlog))
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_normalization_and_explicit_exemptions(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            research = (
                "https://example.test/source#section\n"
                "https://github.com/cntrl-alt-lenny/edopro-retro-formats/blob/main/file.md\n"
                "https://archive.org/download/example/page/n{leaf}\n"
            )
            backlog = _write_fixture(root, research, [{"id": "source", "url": "http://example.test/source/"}], [])
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset()
                self.assertEqual([], check(root, backlog))
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_wayback_redirect_destination_is_explicitly_exempt(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            research = f"http://www.yugioh-card.com/ {REDIRECT_EXEMPTION_MARKER}\n"
            backlog = _write_fixture(root, research, [], [])
            (root / "docs/research/example.md").rename(root / "docs/research/edison-behaviour-gaps.md")
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset()
                self.assertEqual([], check(root, backlog))
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_redirect_destination_exemption_is_scoped_to_its_occurrence(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            research = f"http://www.yugioh-card.com/ {REDIRECT_EXEMPTION_MARKER}\n"
            backlog = _write_fixture(root, research, [], [])
            (root / "docs/research/example.md").rename(root / "docs/research/edison-behaviour-gaps.md")
            (root / "docs/research/other.md").write_text("http://www.yugioh-card.com/\n")
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset()
                errors = check(root, backlog)
                location_errors = [error for error in errors if "not listed in backlog" in error]
                self.assertEqual(1, len(location_errors), errors)
                self.assertIn("docs/research/other.md:1", location_errors[0])
                self.assertNotIn("edison-behaviour-gaps.md", location_errors[0])
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_redirect_destination_exemption_does_not_cover_new_location_in_same_file(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            research = (
                f"Observed redirect: `http://www.yugioh-card.com/` {REDIRECT_EXEMPTION_MARKER}\n"
                "Unrelated note: http://www.yugioh-card.com/\n"
            )
            backlog = _write_fixture(root, research, [], [])
            (root / "docs/research/example.md").rename(root / "docs/research/edison-behaviour-gaps.md")
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset()
                errors = check(root, backlog)
                location_errors = [error for error in errors if "not listed in backlog" in error]
                self.assertEqual(1, len(location_errors), errors)
                self.assertIn("docs/research/edison-behaviour-gaps.md:2", location_errors[0])
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_unrelated_edit_does_not_break_redirect_destination_exemption(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as name:
            root = Path(name)
            research_path = root / "docs/research/example.md"
            backlog = _write_fixture(
                root,
                (
                    f"Observed redirect: `http://www.yugioh-card.com/` {REDIRECT_EXEMPTION_MARKER}\n"
                    "Unrelated note: http://www.yugioh-card.com/\n"
                ),
                [],
                [],
            )
            research_path.rename(root / "docs/research/edison-behaviour-gaps.md")
            target = root / "docs/research/edison-behaviour-gaps.md"
            target.write_text("Unrelated paragraph added above the table.\n\n" + target.read_text())
            import tests.research_citation_registry as registry

            old = registry.BASELINE_UNREGISTERED_URLS
            try:
                registry.BASELINE_UNREGISTERED_URLS = frozenset()
                errors = check(root, backlog)
                location_errors = [error for error in errors if "not listed in backlog" in error]
                self.assertEqual(1, len(location_errors), errors)
                self.assertIn("docs/research/edison-behaviour-gaps.md:4", location_errors[0])
            finally:
                registry.BASELINE_UNREGISTERED_URLS = old

    def test_report_is_green_on_current_tree(self):
        root = Path(__file__).resolve().parents[1]
        self.assertIn("OK", report(root))


if __name__ == "__main__":
    unittest.main()
