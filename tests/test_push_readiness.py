"""Tests for the pre-push readiness gate (scripts/check_push_readiness.py).

The gate this replaced was a Claude Code `PreToolUse` hook that recognised
a push by regex over Bash command text. It was replaced because that layer
could not do the job correctly; `test_command_text_parsing_is_not_how_this_gate_works`
below pins *why*, so nobody reintroduces it.
"""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".githooks" / "pre-push"
SCRIPT = ROOT / "scripts" / "check_push_readiness.py"

sys.path.insert(0, str(ROOT / "scripts"))
from check_push_readiness import CHECKS, check_push_readiness, run_check  # noqa: E402


class PushReadinessTest(unittest.TestCase):
    def test_passes_on_the_real_repository(self):
        """The live repo must be push-ready: this is the gate's happy path,
        and a failure here means main itself is in a state the gate would
        (correctly) refuse to push."""
        exit_code, failures = check_push_readiness()
        self.assertEqual(0, exit_code, "\n\n".join(failures))
        self.assertEqual([], failures)

    def test_runs_exactly_the_checks_ci_runs(self):
        """The gate's value is being the same bar as CI, just earlier. If CI
        gains or drops a data/build check, this must track it."""
        self.assertEqual((("validate",), ("build", "--check")), CHECKS)
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        for args in CHECKS:
            with self.subTest(check=args):
                self.assertIn(" ".join(("python -m retroformats", *args)), ci)

    def test_reports_every_failing_check_not_just_the_first(self):
        """One push attempt should surface every problem, not force a
        fix-push-discover-next-problem loop."""
        broken = ROOT / "tests" / "fixtures"  # a dir with no retroformats package
        exit_code, failures = check_push_readiness(root=broken)
        self.assertEqual(1, exit_code)
        self.assertEqual(
            len(CHECKS),
            len(failures),
            f"expected one report per failing check, got: {failures}",
        )

    def test_failure_report_names_the_command_and_includes_its_output(self):
        broken = ROOT / "tests" / "fixtures"
        _, failures = check_push_readiness(root=broken)
        joined = "\n".join(failures)
        self.assertIn("python -m retroformats validate", joined)
        self.assertIn("exit", joined)

    def test_run_check_surfaces_a_nonzero_exit(self):
        code, output = run_check(("definitely-not-a-subcommand",))
        self.assertNotEqual(0, code)
        self.assertTrue(output.strip(), "a failing check must explain itself")

    def test_main_exits_zero_on_the_real_repository(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)


class PushHookShimTest(unittest.TestCase):
    def test_hook_exists_and_delegates_to_the_tested_script(self):
        """The hook must stay a thin shim -- logic in the hook itself would
        be untestable from here."""
        self.assertTrue(HOOK.is_file(), f"{HOOK} is missing")
        text = HOOK.read_text(encoding="utf-8")
        self.assertIn("scripts/check_push_readiness.py", text)

    def test_hook_handles_both_interpreter_names(self):
        """Windows here has no python3; macOS/Linux commonly have no bare
        python. A hook that hard-codes one silently no-ops on the other."""
        text = HOOK.read_text(encoding="utf-8")
        self.assertIn("python3", text)
        self.assertIn("command -v python", text)

    def test_hook_is_not_wired_as_a_claude_code_bash_hook(self):
        """Regression guard: this gate is vendor-independent by design. A
        Claude Code PreToolUse hook only fires for Claude Code sessions,
        and this project's Worker role is explicitly model-agnostic."""
        settings = ROOT / ".claude" / "settings.json"
        if not settings.is_file():
            self.skipTest("no .claude/settings.json in this checkout")
        text = settings.read_text(encoding="utf-8")
        self.assertNotIn("pre_bash", text)
        self.assertFalse(
            (ROOT / ".claude" / "hooks" / "pre_bash.py").exists(),
            "the regex-based Bash push hook was removed; see this file's docstring",
        )


class CommandTextParsingRegressionTest(unittest.TestCase):
    """Pins why push detection must not be done by parsing command text.

    These are the exact cases the removed `.claude/hooks/pre_bash.py`
    regex got wrong, verified against it before removal. They are recorded
    as a test so that a future attempt to 'just add a quick Bash-level
    guard' has to confront them first.
    """

    # (command, is_actually_a_push)
    CASES = (
        ("git push", True),
        ("git push origin main", True),
        ("cd foo && git push", True),
        ("git -C /some/path push", True),
        ('sh -c "git push"', True),
        ('bash -c "git push origin main"', True),
        ("(git push)", True),
        ("$(git push)", True),
        ("git.exe push", True),
        ('echo "remember to git push later"', False),
        ('git commit -m "docs: explain the git push flow"', False),
    )

    def test_the_old_regex_was_wrong_in_both_directions(self):
        import re

        old = re.compile(r"(^|\s|&&|;|\|)\s*git\s+push\b(?![^\n]*--no-verify)")

        missed = [c for c, is_push in self.CASES if is_push and not old.search(c)]
        false_alarms = [c for c, is_push in self.CASES if not is_push and old.search(c)]

        # Both lists are non-empty: that is the finding, and the reason the
        # gate moved to Git's pre-push layer where no parsing is needed.
        self.assertTrue(missed, "expected the old regex to miss real pushes")
        self.assertTrue(false_alarms, "expected the old regex to fire on non-pushes")
        self.assertIn("git -C /some/path push", missed)
        self.assertIn('git commit -m "docs: explain the git push flow"', false_alarms)


if __name__ == "__main__":
    unittest.main()
