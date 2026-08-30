#!/usr/bin/env python3

"""pre_bash.py -- Claude Code PreToolUse hook for Bash.

Intercepts Bash calls before they run. Currently guards one thing: `git
push`. If a push is about to happen, run `python -m retroformats
validate` and `python -m retroformats build --check` first, and block the
push if either fails. Adapted from a pattern used in a sibling project
(gx-spirit-caller): catch drift before it reaches CI/the remote, while
the agent still has the failing output in front of it and can fix it in
the same turn, instead of finding out from a CI failure notification
several steps later.

Bypass for a one-off case: `SKIP_VALIDATE_HOOK=1 git push ...`, or
`git push --no-verify` (this hook explicitly ignores pushes that already
carry `--no-verify` -- if the agent went out of its way to bypass hooks,
don't second-guess it).

Exit codes:
  0 = continue (non-git-push Bash, or both checks passed)
  2 = block the tool call (PreToolUse semantics -- a check failed)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Match `git push` even with flags/env/chaining around it. Deliberately does
# NOT match a push that already carries --no-verify.
_GIT_PUSH_RE = re.compile(r"(^|\s|&&|;|\|)\s*git\s+push\b(?![^\n]*--no-verify)")


def _read_hook_input() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def _is_git_push(command: str) -> bool:
    return bool(_GIT_PUSH_RE.search(command or ""))


def _run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "retroformats", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    if os.environ.get("SKIP_VALIDATE_HOOK"):
        return 0

    data = _read_hook_input()
    if data.get("tool_name", "") != "Bash":
        return 0
    command = data.get("tool_input", {}).get("command", "")
    if not _is_git_push(command):
        return 0

    validate_rc, validate_out = _run(["validate"])
    build_rc, build_out = _run(["build", "--check"])

    if validate_rc == 0 and build_rc == 0:
        return 0

    print(
        "[pre-bash-hook] `git push` blocked -- validate/build --check failed.\n"
        "Fix each and retry:\n",
        file=sys.stderr,
    )
    if validate_rc != 0:
        print("--- python -m retroformats validate ---", file=sys.stderr)
        print(validate_out, file=sys.stderr)
    if build_rc != 0:
        print("--- python -m retroformats build --check ---", file=sys.stderr)
        print(build_out, file=sys.stderr)
    print(
        "\nBypass once:\n"
        "  SKIP_VALIDATE_HOOK=1 git push ...\n"
        "  # or: git push --no-verify",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
