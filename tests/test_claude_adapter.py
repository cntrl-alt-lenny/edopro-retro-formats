"""Regression tests for the repository's Claude Code adapter mechanics.

WHY THESE TESTS BUILD THEIR OWN GIT STATE. An earlier version of this file
pointed the Worker-checkout guard at `<primary>/.claude/worktrees/worker` (the
executor checkout has since moved to `<primary>/.worktrees/builder`) --
a path that only exists on a machine where someone has already run
`git worktree add`. That is per-clone developer state, not repository
content, so CI errored with FileNotFoundError on a fresh checkout, and the
"accepts the worker worktree" test silently depended on whichever branch
that worktree happened to be sitting on at the time. Tests of checkout
behaviour therefore construct a real temporary repository and a real linked
worktree, and assert against that. Nothing here reads the ambient layout of
the clone it is running in.

The same rule covers the shell: `/bin/sh` is an absolute POSIX path that does
not exist under a native Windows interpreter, so the shell is resolved rather
than assumed. On any POSIX CI runner `sh` is always found, so this resolution
cannot silently skip the coverage that matters.
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_PYTHON = ROOT / ".claude" / "hooks" / "run_python.sh"
WORKER_GUARD = ROOT / ".claude" / "hooks" / "check_worker_checkout.sh"
SETTINGS = ROOT / ".claude" / "settings.json"
WORKER_AGENT = ROOT / ".claude" / "agents" / "worker.md"
SAVE_HOOK = ROOT / ".claude" / "hooks" / "save_agent_reply.py"
REPORT_TOOL = ROOT / "tools" / "report.py"

# Resolve a POSIX shell instead of hard-coding /bin/sh; None means this
# interpreter has no shell to drive the hooks with (native Windows Python
# without Git's shell on PATH), which is a skip, not a failure.
SH = shutil.which("sh") or ("/bin/sh" if os.path.exists("/bin/sh") else None)


def require_shell(case):
    if SH is None:
        case.skipTest("no POSIX shell on PATH; hook scripts cannot be executed here")


def git_output(*args, cwd=ROOT):
    return subprocess.check_output(
        ["git", *args], cwd=str(cwd), text=True
    ).strip()


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True)


def init_repo(path: Path) -> None:
    """A real, minimal git repository -- not a fixture directory."""
    git("init", "-q", cwd=path)
    git("config", "user.email", "t@example.com", cwd=path)
    git("config", "user.name", "t", cwd=path)
    (path / "f").write_text("x\n", encoding="utf-8")
    git("add", "f", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)


def add_worker_worktree(repo: Path, branch: str = "builder/test-round") -> Path:
    """The nested layout the guard requires, created rather than assumed."""
    worktree = repo / ".worktrees" / "builder"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "-q", "-b", branch, str(worktree), "HEAD", cwd=repo)
    return worktree


class PythonHookShimTest(unittest.TestCase):
    def run_shim(self, available):
        require_shell(self)
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            marker = bin_dir / "selected-interpreter"
            for name in available:
                fake = bin_dir / name
                fake.write_text(
                    "#!/bin/sh\n"
                    f"printf '%s' '{name}' > '{marker}'\n",
                    encoding="utf-8",
                )
                fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

            environment = os.environ.copy()
            environment["PATH"] = str(bin_dir)
            process = subprocess.run(
                [SH, str(RUN_PYTHON), "ignored-hook.py"],
                cwd=str(ROOT),
                env=environment,
                capture_output=True,
                text=True,
            )
            marker_contents = marker.read_text(encoding="utf-8") if marker.exists() else None
            return process, marker_contents

    def test_python3_only(self):
        process, marker = self.run_shim(("python3",))
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("python3", marker)

    def test_python_only(self):
        process, marker = self.run_shim(("python",))
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("python", marker)

    def test_both_prefers_python3(self):
        process, marker = self.run_shim(("python3", "python"))
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("python3", marker)

    def test_neither_is_a_clear_nonblocking_skip(self):
        process, marker = self.run_shim(())
        self.assertEqual(0, process.returncode)
        self.assertIsNone(marker)
        self.assertIn("no python3/python", process.stderr)

    def test_stop_hook_uses_shim(self):
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        command = settings["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertEqual(
            "sh .claude/hooks/run_python.sh .claude/hooks/save_agent_reply.py",
            command,
        )
        self.assertNotIn("python .claude/hooks/save_agent_reply.py", command)

    def test_stop_hook_delegates_transcript_text_to_shared_writer(self):
        text = SAVE_HOOK.read_text(encoding="utf-8")
        self.assertIn("import report as _report", text)
        self.assertIn("_report.write_report", text)
        self.assertNotIn("out.write_text", text)


class StopHookDeliveryRegressionTest(unittest.TestCase):
    """The Stop fallback must not destroy a role's own delivery report."""

    TASK = "015-2026-09-16-report-and-materialize-gates"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        init_repo(self.repo)
        (self.repo / "tools").mkdir()
        (self.repo / ".claude" / "hooks").mkdir(parents=True)
        shutil.copyfile(REPORT_TOOL, self.repo / "tools" / "report.py")
        shutil.copyfile(SAVE_HOOK, self.repo / ".claude" / "hooks" / "save_agent_reply.py")
        git("add", "tools/report.py", ".claude/hooks/save_agent_reply.py", cwd=self.repo)
        git("commit", "-q", "-m", "install report adapter", cwd=self.repo)

    def _run_report(self, cwd: Path, *args: str, input_text: str = ""):
        return subprocess.run(
            [sys.executable, str(cwd / "tools" / "report.py"), *args],
            cwd=cwd,
            input=input_text,
            capture_output=True,
            text=True,
        )

    def _delivery(self):
        return subprocess.run(
            [
                sys.executable,
                str(self.repo / "tools" / "report.py"),
                "delivery",
                "--branch",
                "builder/task",
                "--base",
                self.base,
                "--role",
                "builder",
                "--task",
                self.TASK,
            ],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

    def _builder(self):
        builder = self.repo / ".worktrees" / "builder"
        git("worktree", "add", "-q", "-b", "builder/task", str(builder), "HEAD", cwd=self.repo)
        (builder / "change.txt").write_text("delivered\n", encoding="utf-8")
        git("add", "change.txt", cwd=builder)
        git("commit", "-q", "-m", "deliver", cwd=builder)
        return builder

    def _run_hook(self, builder: Path, session_id: str, text: str):
        transcript = self.repo / f"{session_id}.jsonl"
        transcript.write_text(
            json.dumps({"role": "assistant", "content": text}) + "\n",
            encoding="utf-8",
        )
        return subprocess.run(
            [sys.executable, str(builder / ".claude" / "hooks" / "save_agent_reply.py")],
            cwd=builder,
            input=json.dumps({"session_id": session_id, "transcript_path": str(transcript)}),
            capture_output=True,
            text=True,
        )

    def test_later_hook_capture_replaces_earlier_hook_capture_at_same_head(self):
        self.base = git_output("rev-parse", "HEAD", cwd=self.repo)
        builder = self._builder()
        first = self._run_hook(builder, "session-first", "First fallback text.")
        second = self._run_hook(builder, "session-second", "Second fallback text.")
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)

        latest = self.repo / ".git" / "agent-inbox" / "builder-latest.md"
        latest_text = latest.read_text(encoding="utf-8")
        self.assertIn("task=claude-code-session:session-second", latest_text)
        self.assertIn("Second fallback text.", latest_text)
        self.assertNotIn("First fallback text.", latest_text)

        log = (self.repo / ".git" / "agent-inbox" / "builder-log.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("First fallback text.", log)
        self.assertIn("Second fallback text.", log)

    def test_real_stop_hook_preserves_own_report_for_real_delivery_check(self):
        self.base = git_output("rev-parse", "HEAD", cwd=self.repo)
        builder = self._builder()
        report = self._run_report(builder, "write", "--task", self.TASK,
                                  input_text="Builder's own completion report.\n")
        self.assertEqual(0, report.returncode, report.stderr)

        transcript = self.repo / "transcript.jsonl"
        transcript.write_text(
            json.dumps({"role": "assistant", "content": "Stop fallback text."}) + "\n",
            encoding="utf-8",
        )
        hook = subprocess.run(
            [sys.executable, str(builder / ".claude" / "hooks" / "save_agent_reply.py")],
            cwd=builder,
            input=json.dumps({"session_id": "session-123", "transcript_path": str(transcript)}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, hook.returncode, hook.stderr)

        latest = self.repo / ".git" / "agent-inbox" / "builder-latest.md"
        self.assertIn("task=" + self.TASK, latest.read_text(encoding="utf-8"))
        self.assertIn("Builder's own completion report.", latest.read_text(encoding="utf-8"))
        self.assertNotIn("claude-code-session:session-123", latest.read_text(encoding="utf-8"))
        delivery = self._delivery()
        self.assertEqual(0, delivery.returncode, delivery.stdout + delivery.stderr)
        self.assertIn("delivered:", delivery.stdout)

    def test_session_tagged_fallback_still_fails_delivery(self):
        self.base = git_output("rev-parse", "HEAD", cwd=self.repo)
        builder = self._builder()
        transcript = self.repo / "transcript.jsonl"
        transcript.write_text(
            json.dumps({"role": "assistant", "content": "No contract report."}) + "\n",
            encoding="utf-8",
        )
        hook = subprocess.run(
            [sys.executable, str(builder / ".claude" / "hooks" / "save_agent_reply.py")],
            cwd=builder,
            input=json.dumps({"session_id": "session-456", "transcript_path": str(transcript)}),
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, hook.returncode, hook.stderr)
        latest = self.repo / ".git" / "agent-inbox" / "builder-latest.md"
        self.assertIn("task=claude-code-session:session-456", latest.read_text(encoding="utf-8"))
        delivery = self._delivery()
        self.assertEqual(1, delivery.returncode, delivery.stdout + delivery.stderr)
        self.assertIn("not delivered yet", delivery.stdout)


class WorkerCheckoutGuardTest(unittest.TestCase):
    """Drives the real guard script against a repository built here."""

    def setUp(self):
        require_shell(self)
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._tmp.cleanup)
        # resolve(): the guard compares paths after `pwd -P`, so the fixture
        # must be compared in the same resolved form (macOS /var -> /private/var).
        self.primary = Path(self._tmp.name).resolve()
        init_repo(self.primary)
        self.worker = add_worker_worktree(self.primary)

    def run_guard(self, cwd, extra_environment=None):
        environment = os.environ.copy()
        if extra_environment:
            environment.update(extra_environment)
        return subprocess.run(
            [SH, str(WORKER_GUARD)],
            cwd=str(cwd),
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_rejects_primary_checkout_fail_closed(self):
        process = self.run_guard(
            self.primary,
            {"WORKTREE": str(self.worker), "EXPECTED_WORKTREE": str(self.worker)},
        )
        self.assertEqual(2, process.returncode)
        self.assertIn("do not run Builder from Brain's primary checkout", process.stderr)
        # The message must still point at where to go instead. Assert the
        # nested-worktree suffix rather than a full path: the guard reports
        # `pwd -P` output, whose spelling differs from Python's str(Path) on
        # Windows, and pinning that spelling is what makes a test machine-bound.
        self.assertIn(".worktrees/builder", process.stderr.replace("\\", "/"))
        self.assertIn("current checkout:", process.stderr)

    def test_accepts_nested_worker_worktree_on_worker_branch(self):
        process = self.run_guard(self.worker)
        self.assertEqual(0, process.returncode, process.stderr)

    def test_rejects_the_worker_worktree_on_a_non_worker_branch(self):
        git("checkout", "-q", "-b", "worker/not-a-builder-branch", cwd=self.worker)
        process = self.run_guard(self.worker)
        self.assertEqual(2, process.returncode)

    def test_rejects_a_detached_head_in_the_worker_worktree(self):
        git("checkout", "-q", "--detach", "HEAD", cwd=self.worker)
        process = self.run_guard(self.worker)
        self.assertEqual(2, process.returncode)

    def test_agent_wires_a_blocking_prompt_guard(self):
        text = WORKER_AGENT.read_text(encoding="utf-8")
        self.assertIn("hooks:\n  UserPromptSubmit:", text)
        self.assertIn('command: "sh .claude/hooks/check_worker_checkout.sh"', text)
        self.assertNotIn("check_worker_checkout.sh", SETTINGS.read_text(encoding="utf-8"))

    def test_guard_derives_checkout_and_branch_from_git(self):
        text = WORKER_GUARD.read_text(encoding="utf-8")
        self.assertIn("git rev-parse --show-toplevel", text)
        self.assertIn("git rev-parse --git-common-dir", text)
        self.assertIn("git symbolic-ref --quiet --short HEAD", text)
        self.assertIn("builder/*", text)


class TrackedHookModeTest(unittest.TestCase):
    def test_pre_push_is_tracked_executable(self):
        entry = git_output("ls-files", "-s", "--", ".githooks/pre-push")
        self.assertTrue(entry.startswith("100755 "), entry)


if __name__ == "__main__":
    unittest.main()
