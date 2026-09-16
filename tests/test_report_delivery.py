"""The Verifier's delivery gate: `tools/report.py delivery`.

Ported from the framework repository's own `tests/test_owner_loop.py`
(`TestDeliveryCommand`), because adoption installs `tools/report.py` with its
`delivery` subcommand but does not install any test that exercises it. The
Verifier contract (docs/agents/roles/verifier.md) makes this check the thing
that separates "a branch exists" from "the Builder delivered", so it must not
ride in untested. Class body is verbatim apart from resolving ROOT here.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestDeliveryCommand(unittest.TestCase):
    """The Verifier gate must distinguish branch existence from delivery."""

    TASK = "round-002"

    def _git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    def _repo(self) -> tuple[tempfile.TemporaryDirectory, Path, str]:
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        self._git(repo, "init", "-q", "-b", "main")
        self._git(repo, "config", "user.email", "test@example.invalid")
        self._git(repo, "config", "user.name", "Test")
        (repo / "README.md").write_text("base\n", encoding="utf-8")
        self._git(repo, "add", "README.md")
        self._git(repo, "commit", "-q", "-m", "base")
        return tmp, repo, self._git(repo, "rev-parse", "HEAD")

    def _check(self, repo: Path, base: str):
        return subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "delivery",
                "--branch", "worker/task", "--base", base,
                "--role", "builder", "--task", self.TASK,
            ],
            cwd=repo, capture_output=True, text=True,
        )

    def test_not_yet_pushed_branch_is_not_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not delivered yet", proc.stdout)

    def test_pushed_at_base_branch_is_not_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "branch", "worker/task", base)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("still at the base", proc.stdout)

    def test_report_and_advanced_branch_are_delivered(self):
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "branch", "worker/task", base)
        builder = repo / ".worktrees" / "builder"
        self._git(repo, "worktree", "add", "-q", str(builder), "worker/task")
        (builder / "change.txt").write_text("delivered\n", encoding="utf-8")
        self._git(builder, "add", "change.txt")
        self._git(builder, "commit", "-q", "-m", "deliver")
        report = subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "write",
                "--task", self.TASK,
            ],
            cwd=builder, input="Builder delivered.\n", capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("delivered:", proc.stdout)

    def test_separate_clones_discover_delivery_only_after_builder_pushes(self):
        """The fetch is exercised against a real bare remote and two clones."""
        tmp, seed, base = self._repo()
        self.addCleanup(tmp.cleanup)
        remote = Path(tmp.name) / "origin.git"
        self._git(seed, "init", "--bare", "-q", str(remote))
        self._git(seed, "remote", "add", "origin", str(remote))
        self._git(seed, "push", "-q", "origin", "main")

        builder = Path(tmp.name) / "builder"
        verifier = Path(tmp.name) / "verifier"
        subprocess.run(
            ["git", "clone", "-q", "-b", "main", str(remote), str(builder)],
            check=True,
        )
        subprocess.run(
            ["git", "clone", "-q", "-b", "main", str(remote), str(verifier)],
            check=True,
        )
        for clone in (builder, verifier):
            self._git(clone, "config", "user.email", "test@example.invalid")
            self._git(clone, "config", "user.name", "Test")
        self._git(verifier, "branch", "worker/task", base)

        self._git(builder, "switch", "-c", "worker/task")
        self._git(builder, "switch", "main")
        builder_checkout = builder / ".worktrees" / "builder"
        self._git(builder, "worktree", "add", "-q", str(builder_checkout), "worker/task")
        (builder_checkout / "change.txt").write_text(
            "delivered\n", encoding="utf-8"
        )
        self._git(builder_checkout, "add", "change.txt")
        self._git(builder_checkout, "commit", "-q", "-m", "deliver")
        report = subprocess.run(
            [
                sys.executable, str(ROOT / "tools" / "report.py"), "write",
                "--task", self.TASK,
            ],
            cwd=builder_checkout, input="Builder delivered.\n",
            capture_output=True, text=True,
        )
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)

        verifier_inbox = verifier / ".git" / "agent-inbox"
        verifier_inbox.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            builder / ".git" / "agent-inbox" / "builder-latest.md",
            verifier_inbox / "builder-latest.md",
        )

        before_push = self._check(verifier, base)
        self.assertEqual(before_push.returncode, 1, before_push.stdout)
        self.assertIn("not delivered yet", before_push.stdout)

        self._git(builder_checkout, "push", "-q", "-u", "origin", "worker/task")
        after_push = self._check(verifier, base)
        self.assertEqual(after_push.returncode, 0, after_push.stdout + after_push.stderr)
        self.assertIn("delivered:", after_push.stdout)

    def test_diverged_local_branch_is_retryable_and_explains_the_conflict(self):
        tmp, seed, base = self._repo()
        self.addCleanup(tmp.cleanup)
        remote = Path(tmp.name) / "origin.git"
        self._git(seed, "init", "--bare", "-q", str(remote))
        self._git(seed, "remote", "add", "origin", str(remote))
        self._git(seed, "push", "-q", "origin", "main")

        builder = Path(tmp.name) / "builder"
        verifier = Path(tmp.name) / "verifier"
        for clone in (builder, verifier):
            subprocess.run(
                ["git", "clone", "-q", "-b", "main", str(remote), str(clone)],
                check=True,
            )
            self._git(clone, "config", "user.email", "test@example.invalid")
            self._git(clone, "config", "user.name", "Test")

        self._git(builder, "switch", "-c", "worker/task")
        (builder / "remote.txt").write_text("remote\n", encoding="utf-8")
        self._git(builder, "add", "remote.txt")
        self._git(builder, "commit", "-q", "-m", "remote delivery")
        remote_head = self._git(builder, "rev-parse", "HEAD")
        self._git(builder, "push", "-q", "-u", "origin", "worker/task")

        self._git(verifier, "switch", "-c", "worker/task")
        (verifier / "local.txt").write_text("local\n", encoding="utf-8")
        self._git(verifier, "add", "local.txt")
        self._git(verifier, "commit", "-q", "-m", "local divergence")
        proc = self._check(verifier, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("diverges", proc.stdout)
        self.assertIn(remote_head, proc.stdout)

    def test_unreachable_remote_stays_retryable(self):
        """Regression coverage: this passed before the fetch/reconciliation fix."""
        tmp, repo, base = self._repo()
        self.addCleanup(tmp.cleanup)
        self._git(repo, "remote", "add", "origin", str(Path(tmp.name) / "missing.git"))
        proc = self._check(repo, base)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("not delivered yet", proc.stdout)
        self.assertNotIn("Traceback", proc.stdout + proc.stderr)



if __name__ == "__main__":
    unittest.main()
