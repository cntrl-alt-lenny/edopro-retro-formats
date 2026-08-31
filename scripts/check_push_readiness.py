#!/usr/bin/env python3

"""Pre-push readiness check: canonical data validates, generated output is fresh.

Invoked by `.githooks/pre-push` (see docs/agents/push-gate.md). Runs the
same two commands CI runs before anything reaches the remote:

    python -m retroformats validate
    python -m retroformats build --check

and fails the push if either does. The point is early feedback: catching
validator errors or `dist/` drift while the agent or human still has the
failing output in front of them, rather than finding out from a CI run
several steps later.

# Why this lives at Git's pre-push layer

An earlier version of this check was a Claude Code `PreToolUse` hook that
tried to recognise a push by regex over the Bash command text. That layer
was wrong for two independent reasons, both verified against the actual
implementation before it was replaced:

1. **It missed ordinary pushes.** `git -C <path> push`, `sh -c "git
   push"`, `bash -c "..."`, `(git push)`, `$(git push)` and `git.exe push`
   all bypassed the regex, because it required a literal `git` followed by
   whitespace and `push` preceded by a start/space/`&&`/`;`/`|`.
2. **It blocked things that were not pushes.** Any Bash command merely
   *containing* the phrase — notably `git commit -m "...git push..."`,
   which this project's own commit messages do — matched and was blocked.

At the pre-push layer Git has already decided that a push is happening and
resolved what is being pushed, so neither failure mode is reachable: there
is no command text to parse. It is also vendor-independent — it fires for
any git client (a Claude Code session, another vendor's agent tool, a
plain terminal, an IDE), which matters because this project's Worker role
is explicitly model-agnostic and a non-Claude Worker never triggered the
old hook at all.

# What this is NOT

**A local hook is a convenience, not a control.** It is opt-in per clone
(`git config core.hooksPath .githooks`), trivially bypassed with `git push
--no-verify`, and absent entirely on a fresh clone until configured. There
is no server-side enforcement behind it — this repository has no
pre-receive hook or equivalent guarantee. CI
(`.github/workflows/ci.yml`, which runs these same commands plus the test
suite on every push and PR) remains the only backstop that actually always
runs. Do not treat a green local hook as proof that anything is enforced.

# Scope limitations

Two, both verified by deliberately breaking things and observing what this
gate did and did not catch:

1. **It validates the *current checkout*, not each pushed commit.** For
   this project's workflow (short-lived `worker/<slug>` branches pushed
   from a clean tree) that is the useful check. A push from a dirty tree,
   or of commits whose intermediate states differ from the tip, is not
   individually verified here; CI covers the pushed tip.
2. **`build --check` regenerates `dist/` before comparing, so an
   *uncommitted* hand-edit to `dist/` is silently overwritten rather than
   reported.** What it actually catches is the case that matters:
   committed `dist/` content that disagrees with what canonical data
   generates — whether because canonical data changed without a rebuild,
   or because someone committed a hand-edit. Do not read a passing check
   as "nobody touched dist/ in my working tree."
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS: tuple[tuple[str, ...], ...] = (
    ("validate",),
    ("build", "--check"),
)


def run_check(args: tuple[str, ...], root: Path | None = None) -> tuple[int, str]:
    """Run `python -m retroformats <args>` and return (returncode, output)."""
    proc = subprocess.run(
        [sys.executable, "-m", "retroformats", *args],
        cwd=str(root or ROOT),
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check_push_readiness(root: Path | None = None) -> tuple[int, list[str]]:
    """Run every readiness check.

    Returns (exit_code, failure_reports). exit_code is 0 when all checks
    pass, 1 otherwise. Every check runs even if an earlier one fails, so a
    single push attempt reports all problems rather than one per retry.
    """
    failures: list[str] = []
    for args in CHECKS:
        code, output = run_check(args, root)
        if code != 0:
            label = " ".join(("python -m retroformats", *args))
            failures.append(f"--- {label} (exit {code}) ---\n{output}")
    return (1 if failures else 0), failures


def main() -> int:
    exit_code, failures = check_push_readiness()
    if exit_code == 0:
        return 0
    print(
        "[pre-push] push blocked -- canonical data or generated output is not ready.\n"
        "Fix each and retry:\n",
        file=sys.stderr,
    )
    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        "\nBypass once (does not skip CI, which runs the same checks):\n"
        "  git push --no-verify",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
