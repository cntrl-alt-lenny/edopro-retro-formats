"""Tests for the engine-CI helper (scripts/engine_env.py) and the workflow that uses it.

The engine job exists so the duel-engine tests run for real instead of skipping
everywhere. What this pins is what would let it quietly go back to that: a gate
that accepts a skip, pins that stop being full commit hashes, a checkout that no
longer has to equal its pin, or a workflow that runs the engine tests without
the gate. None of it touches the network.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import engine_env  # noqa: E402

CI = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def _job(name: str) -> str:
    """One top-level job in ci.yml (a 2-space-indented key under jobs:), comments removed."""
    match = re.search(rf"^  {name}:\n(.*?)(?=^  [A-Za-z_-]+:\n|\Z)", CI, re.S | re.M)
    assert match, f"no job {name!r} in ci.yml"
    return "".join(line for line in match.group(1).splitlines(keepends=True) if not line.lstrip().startswith("#"))


def _run(*cases: str) -> unittest.TestResult:
    """Run throwaway TestCases by name.

    They are built inside this function on purpose: as module-level classes
    the main suite's discovery would collect them and report their deliberate
    failures and skips as the project's own.
    """

    class Passes(unittest.TestCase):
        def test_a(self):
            pass

        def test_b(self):
            pass

    class SkipsOne(unittest.TestCase):
        def test_a(self):
            pass

        @unittest.skip("forced")
        def test_b(self):
            pass

    @unittest.skip("the whole class, like a missing engine")
    class SkipsAll(unittest.TestCase):
        def test_a(self):
            pass

        def test_b(self):
            pass

    class Fails(unittest.TestCase):
        def test_a(self):
            self.fail("wrong behaviour")

    class ExpectedFailure(unittest.TestCase):
        @unittest.expectedFailure
        def test_a(self):
            self.fail("tolerated")

    available = {c.__name__: c for c in (Passes, SkipsOne, SkipsAll, Fails, ExpectedFailure)}
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(available[n]) for n in cases)
    return unittest.TextTestRunner(stream=io.StringIO()).run(suite)


class GateTest(unittest.TestCase):
    def test_a_full_pass_is_accepted(self):
        self.assertEqual([], engine_env.evaluate_result(_run("Passes"), expect_at_least=2))

    def test_one_skip_fails_the_gate_even_though_unittest_calls_it_ok(self):
        result = _run("SkipsOne")
        self.assertTrue(result.wasSuccessful(), "premise: plain unittest treats a skip as success")
        problems = engine_env.evaluate_result(result, expect_at_least=1)
        self.assertTrue(any("skipped" in p for p in problems), problems)

    def test_everything_skipping_fails_the_gate(self):
        """The bare-runner state this whole job exists to remove."""
        result = _run("SkipsAll")
        self.assertTrue(result.wasSuccessful())
        problems = engine_env.evaluate_result(result, expect_at_least=2)
        self.assertTrue(any("skipped" in p for p in problems), problems)
        self.assertTrue(any("executed" in p for p in problems), problems)

    def test_failures_fail_the_gate(self):
        self.assertTrue(engine_env.evaluate_result(_run("Fails"), expect_at_least=1))

    def test_expected_failures_do_not_count_as_passing(self):
        problems = engine_env.evaluate_result(_run("ExpectedFailure"), expect_at_least=0)
        self.assertTrue(any("expected failure" in p for p in problems), problems)

    def test_fewer_executed_tests_than_required_fails_the_gate(self):
        """Deleting or failing to discover engine tests must not go green."""
        problems = engine_env.evaluate_result(_run("Passes"), expect_at_least=3)
        self.assertTrue(any("only 2" in p for p in problems), problems)


class PinsTest(unittest.TestCase):
    def test_pins_are_the_recorded_full_commits(self):
        sources = {s["id"]: s for s in json.loads((ROOT / "data" / "sources.json").read_text("utf-8"))["sources"]}
        pins = engine_env.load_pins()
        self.assertEqual({"babelcdb", "cardscripts", "core"}, set(pins))
        for name, source_id in engine_env.PINNED_REPOS.items():
            url, revision = pins[name]
            self.assertEqual(sources[source_id]["revision"], revision)
            self.assertRegex(revision, r"^[0-9a-f]{40}$")
            self.assertTrue(url.startswith("https://github.com/"), url)

    def test_a_pin_that_is_not_a_full_commit_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            records = [
                {"id": "ignis-babelcdb", "url": "https://github.com/x/y", "revision": "main"},
                {"id": "ignis-cardscripts", "url": "https://github.com/x/y", "revision": "0" * 40},
                {"id": "ygopro-core", "url": "https://github.com/x/y", "revision": "0" * 40},
            ]
            path.write_text(json.dumps({"sources": records}), encoding="utf-8")
            with self.assertRaisesRegex(engine_env.EngineEnvError, "not a full 40-hex commit"):
                engine_env.load_pins(path)

    def test_premake_checksums_are_full_sha256(self):
        self.assertEqual({"linux", "macosx"}, set(engine_env.PREMAKE_SHA256))
        for digest in engine_env.PREMAKE_SHA256.values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")


class VerifyCheckoutTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)

        def git(*args):
            return subprocess.run(
                ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                cwd=self.repo, capture_output=True, text=True, check=True,
            ).stdout.strip()

        git("init", "-q")
        (self.repo / "script.lua").write_text("original\n", encoding="utf-8")
        git("add", "script.lua")
        git("commit", "-q", "-m", "pin")
        self.pin = git("rev-parse", "HEAD")

    def test_the_pinned_revision_verifies(self):
        engine_env.verify_checkout(self.repo, self.pin)

    def test_a_different_revision_is_refused(self):
        with self.assertRaisesRegex(engine_env.EngineEnvError, "expected pinned"):
            engine_env.verify_checkout(self.repo, "0" * 40)

    def test_a_modified_tracked_file_is_refused(self):
        (self.repo / "script.lua").write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(engine_env.EngineEnvError, "modified tracked files"):
            engine_env.verify_checkout(self.repo, self.pin)

    def test_a_directory_that_is_not_a_checkout_is_refused(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(engine_env.EngineEnvError, "not a git checkout"):
                engine_env.verify_checkout(Path(empty), self.pin)


class WorkflowTest(unittest.TestCase):
    def test_the_existing_job_still_runs_exactly_what_it_ran(self):
        job = _job("check")
        self.assertIn('python-version: ["3.10", "3.13"]', job)
        self.assertIn("fetch-depth: 0", job)
        self.assertEqual(
            [
                "python -m retroformats validate",
                "python -m retroformats build --check",
                "python -m unittest discover -t . -s tests -v",
            ],
            re.findall(r"^\s+run: (.+)$", job, re.M),
        )
        self.assertNotIn("engine", job, "engine work belongs in its own job, not the main one")

    def test_the_engine_job_goes_through_the_no_skip_gate_not_plain_unittest(self):
        """Plain `unittest` exits 0 with every test skipped; only the gate does not."""
        job = _job("engine")
        self.assertIn("scripts/engine_env.py prepare", job)
        self.assertRegex(job, r"scripts/engine_env\.py run .*--expect-at-least \d+")
        self.assertNotIn("unittest", job)

    def test_the_required_count_is_the_number_of_engine_tests(self):
        """Neither a deleted test nor an unbumped new one may leave the floor stale."""
        required = int(re.search(r"--expect-at-least (\d+)", _job("engine")).group(1))
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "engine"), top_level_dir=str(ROOT))
        self.assertEqual(suite.countTestCases(), required)


if __name__ == "__main__":
    unittest.main()
