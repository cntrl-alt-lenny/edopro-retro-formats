"""Regression tests for the repository's Claude Code adapter mechanics."""

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_PYTHON = ROOT / ".claude" / "hooks" / "run_python.sh"
WORKER_GUARD = ROOT / ".claude" / "hooks" / "check_worker_checkout.sh"
SETTINGS = ROOT / ".claude" / "settings.json"
WORKER_AGENT = ROOT / ".claude" / "agents" / "worker.md"
SAVE_HOOK = ROOT / ".claude" / "hooks" / "save_agent_reply.py"


def git_output(*args, cwd=ROOT):
    return subprocess.check_output(
        ["git", *args], cwd=str(cwd), text=True
    ).strip()


COMMON_DIR = Path(git_output("rev-parse", "--git-common-dir"))
if not COMMON_DIR.is_absolute():
    COMMON_DIR = (ROOT / COMMON_DIR).resolve()
PRIMARY = COMMON_DIR.resolve().parent
WORKER = PRIMARY / ".claude" / "worktrees" / "worker"


class PythonHookShimTest(unittest.TestCase):
    def run_shim(self, available):
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
                ["/bin/sh", str(RUN_PYTHON), "ignored-hook.py"],
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


class WorkerCheckoutGuardTest(unittest.TestCase):
    def run_guard(self, cwd, extra_environment=None):
        environment = os.environ.copy()
        if extra_environment:
            environment.update(extra_environment)
        return subprocess.run(
            ["/bin/sh", str(WORKER_GUARD)],
            cwd=str(cwd),
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_rejects_primary_checkout_fail_closed(self):
        process = self.run_guard(
            PRIMARY,
            {"WORKTREE": str(WORKER), "EXPECTED_WORKTREE": str(WORKER)},
        )
        self.assertEqual(2, process.returncode)
        self.assertIn(str(WORKER), process.stderr)
        self.assertIn(str(PRIMARY), process.stderr)
        self.assertIn("do not run Worker from Brain's primary checkout", process.stderr)

    def test_accepts_nested_worker_worktree_on_worker_branch(self):
        process = self.run_guard(WORKER)
        self.assertEqual(0, process.returncode, process.stderr)

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
        self.assertIn("worker/*", text)


class TrackedHookModeTest(unittest.TestCase):
    def test_pre_push_is_tracked_executable(self):
        entry = git_output("ls-files", "-s", "--", ".githooks/pre-push")
        self.assertTrue(entry.startswith("100755 "), entry)


if __name__ == "__main__":
    unittest.main()
