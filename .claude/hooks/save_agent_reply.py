#!/usr/bin/env python3

"""save_agent_reply.py -- Claude Code Stop hook.

Captures the final assistant turn of a Claude Code session and writes it
to a shared inbox so a Brain session can read what a Worker session said
without the human copy-pasting it in chat. Adapted from a pattern used in
a sibling project (gx-spirit-caller); see docs/agents/worktree-mechanism.md
for the worktree layout this depends on.

# Why this exists

Brain and Worker run in separate worktrees of the same clone — Brain in
the primary checkout, Worker in the nested `.claude/worktrees/worker/`
(see docs/agents/worktree-mechanism.md). When a Worker round
ends without the human relaying a report, Brain has no way to see what
happened except by re-deriving it from the diff -- fine for facts, but it
loses whatever Worker said about things it was unsure of, blockers it
hit, or scope it deliberately left out. This hook closes that gap: every
time a session ends, its last assistant turn is appended to
`<shared-git-dir>/agent-inbox/<role>-latest.md`.

# IMPORTANT CAVEAT -- this only fires for Claude Code sessions

This is Claude Code's own Stop-hook protocol (a JSON event on stdin,
listed in .claude/settings.json). It does NOT fire for a Worker round run
in a different vendor's tool (this project's Worker role is explicitly
model-agnostic -- see AGENTS.md -- and the human sometimes runs a brief
through a different frontier model's own CLI/agent product). In that
case this hook simply never runs, and the human relaying the report (as
before) is still the way Brain finds out. Don't assume the inbox file is
current -- check its timestamp, and don't treat a missing/stale inbox
file as "nothing happened."

# Why these path/role choices

- `git rev-parse --git-common-dir` gives the repo's shared `.git/` path --
  the same value from either worktree, regardless of where the clone
  lives on disk.
- `<git-common-dir>/agent-inbox/` sits inside `.git/`, which git never
  version-controls and treats as private. No .gitignore entry needed; it
  survives `git clean -fdx` and disappears cleanly if the clone is ever
  removed.
- Role is inferred from whether the current worktree's path runs through
  `.claude/worktrees/`: if it does, role is `worker`; the primary checkout
  (no such path segment) is role `brain`. This matches
  docs/agents/worktree-mechanism.md's fixed layout (Worker's nested
  worktree lives at `.claude/worktrees/worker/`). If the human changes
  that layout, update this mapping.

# Hook event input

Claude Code passes a JSON event on stdin to Stop hooks. Only
`transcript_path` is needed. If the event is missing it (older Claude
Code, a manual test invocation), the hook exits silently -- Stop hooks
must never block a session from ending.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]


def _git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(_REPO), *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _last_assistant_text(transcript_path: Path) -> str | None:
    try:
        lines = transcript_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None

    last_assistant = None
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = entry.get("role") or entry.get("message", {}).get("role")
        if role == "assistant":
            last_assistant = entry

    if last_assistant is None:
        return None

    content = last_assistant.get("content") or (
        last_assistant.get("message", {}).get("content")
    )
    if isinstance(content, str):
        return content.strip() or None
    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str):
                parts.append(text)
    out = "\n".join(parts).strip()
    return out or None


def _role_from_worktree(worktree_root: str | None) -> str:
    if not worktree_root:
        return "unknown"
    parts = Path(worktree_root).parts
    return "worker" if ".claude" in parts and "worktrees" in parts else "brain"


def _seed_readme(inbox: Path) -> None:
    readme = inbox / "README.md"
    if readme.exists():
        return
    readme.write_text(
        "# .git/agent-inbox/\n\n"
        "Auto-populated by `.claude/hooks/save_agent_reply.py` (a Stop\n"
        "hook, Claude Code sessions only -- see that script's docstring).\n"
        "`<role>-latest.md` holds the final assistant turn of the most\n"
        "recent Claude Code session in the matching worktree (`brain` or\n"
        "`worker`); `<role>-log.md` is the append-only history.\n\n"
        "Read these to see what the other side said without the human\n"
        "shuttling text manually -- but check the timestamp: a Worker\n"
        "round run through a non-Claude-Code tool never writes here.\n\n"
        "Not under version control (lives inside `.git/`). Wipes cleanly\n"
        "with a fresh clone.\n",
        encoding="utf-8",
    )


def main() -> int:
    try:
        raw = sys.stdin.read()
    except (OSError, KeyboardInterrupt):
        return 0
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    transcript = event.get("transcript_path")
    if not transcript:
        return 0
    transcript_path = Path(transcript)
    if not transcript_path.exists():
        return 0

    text = _last_assistant_text(transcript_path)
    if not text:
        return 0

    common_dir = _git(["rev-parse", "--git-common-dir"])
    if not common_dir:
        return 0
    common = Path(common_dir)
    if not common.is_absolute():
        common = (_REPO / common).resolve()
    inbox = common / "agent-inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    _seed_readme(inbox)

    worktree_root = _git(["rev-parse", "--show-toplevel"])
    role = _role_from_worktree(worktree_root)

    session_id = event.get("session_id", "")
    ts = datetime.now().isoformat(timespec="seconds")
    header = (
        f"<!-- captured {ts} from worktree role={role}"
        f"{f' session={session_id}' if session_id else ''} -->\n\n"
    )

    out = inbox / f"{role}-latest.md"
    try:
        out.write_text(header + text + "\n", encoding="utf-8")
    except OSError:
        return 0

    log = inbox / f"{role}-log.md"
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{header}{text}\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
