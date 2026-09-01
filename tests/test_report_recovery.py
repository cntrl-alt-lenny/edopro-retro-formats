"""Behavioural tests for provider transcript recovery."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "recover_agent_report.py"
sys.path.insert(0, str(ROOT / "tools"))
import recover_agent_report  # noqa: E402


def run_git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    ).stdout.strip()


class RecoveryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        run_git("init", "-q", cwd=self.repo)
        run_git("config", "user.email", "test@example.com", cwd=self.repo)
        run_git("config", "user.name", "test", cwd=self.repo)
        (self.repo / "f").write_text("fixture\n", encoding="utf-8")
        run_git("add", "f", cwd=self.repo)
        run_git("commit", "-q", "-m", "fixture", cwd=self.repo)
        self.sha = run_git("rev-parse", "HEAD", cwd=self.repo)
        self.commit_time = int(run_git("show", "-s", "--format=%ct", cwd=self.repo))
        self.worker = self.repo / ".worktrees" / "worker"
        self.worker.parent.mkdir()
        run_git("worktree", "add", "--detach", str(self.worker), "HEAD", cwd=self.repo)
        self.store = self.root / "provider-store"
        self.store_path = self.store / "a" / "b" / "c" / "rollout-one.jsonl"
        self.store_path.parent.mkdir(parents=True)
        self.config_path = self.repo / ".git" / "agent-inbox" / "providers.local.json"
        self.config_path.parent.mkdir()
        self.addCleanup(self.temp.cleanup)

    def configure(self, store=None):
        provider_root = str(store or self.store)
        self.config_path.write_text(
            json.dumps(
                {
                    "providers": {
                        "codex": {
                            "kind": "jsonl-rollouts",
                            "root": provider_root,
                            "glob": "*/*/*/rollout-*.jsonl",
                            "status": "supported",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

    def session(self, *, cwd, mtime, message="worker report", session="worker-1"):
        self.store_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "type": "session_meta",
                            "payload": {
                                "id": session,
                                "cwd": str(cwd),
                                "git": {"branch": "worker/fixture"},
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "event_msg",
                            "payload": {
                                "type": "task_complete",
                                "last_agent_message": message,
                                "round": self.sha,
                            },
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        os.utime(self.store_path, (mtime, mtime))

    def recover(self, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(self.repo),
                "--sha",
                self.sha,
                "--provider",
                "codex",
                *extra,
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )


class RecoveryRuleTest(RecoveryFixture):
    def test_exact_fifteen_minute_boundary_is_accepted(self):
        self.configure()
        self.session(cwd=self.worker, mtime=self.commit_time + recover_agent_report.DEFAULT_MAX_LAG)
        process = self.recover()
        self.assertEqual(0, process.returncode, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual("worker-1", result["session"])
        self.assertEqual(recover_agent_report.DEFAULT_MAX_LAG, result["seconds_after_commit"])

    def test_one_second_beyond_boundary_is_unknown(self):
        self.configure()
        self.session(cwd=self.worker, mtime=self.commit_time + recover_agent_report.DEFAULT_MAX_LAG + 1)
        process = self.recover()
        self.assertEqual(1, process.returncode)
        self.assertEqual("", process.stdout)
        self.assertIn("UNKNOWN", process.stderr)
        self.assertIn("within 900s", process.stderr)

    def test_brains_primary_session_is_never_returned(self):
        self.configure()
        self.session(cwd=self.repo, mtime=self.commit_time + 1, session="brain-live")
        process = self.recover()
        self.assertEqual(1, process.returncode)
        self.assertIn("UNKNOWN", process.stderr)
        self.assertIn("no session", process.stderr)
        self.assertNotIn("brain-live", process.stdout + process.stderr)

    def test_a_round_produced_off_machine_is_unknown(self):
        self.configure()
        self.session(
            cwd=self.root / "other-clone",
            mtime=self.commit_time + 1,
            session="off-machine",
        )
        process = self.recover()
        self.assertEqual(1, process.returncode)
        self.assertIn("UNKNOWN", process.stderr)
        self.assertNotIn("off-machine", process.stdout + process.stderr)

    def test_missing_provider_config_is_unknown(self):
        process = self.recover()
        self.assertEqual(3, process.returncode)
        self.assertIn("UNKNOWN", process.stderr)
        self.assertIn("providers.local.json", process.stderr)

    def test_a_later_session_mentioning_the_sha_is_not_selected(self):
        self.configure()
        self.session(cwd=self.worker, mtime=self.commit_time + 10, session="producer")
        later = self.store / "a" / "b" / "c" / "rollout-later.jsonl"
        later.write_text(self.store_path.read_text(encoding="utf-8").replace("worker-1", "later"), encoding="utf-8")
        os.utime(later, (self.commit_time + recover_agent_report.DEFAULT_MAX_LAG + 1,) * 2)
        process = self.recover()
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("producer", json.loads(process.stdout)["session"])


if __name__ == "__main__":
    unittest.main()
