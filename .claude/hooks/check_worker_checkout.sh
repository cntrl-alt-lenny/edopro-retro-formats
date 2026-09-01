#!/bin/sh

# This is a blocking Claude Code UserPromptSubmit hook. Derive the required
# checkout from Git's common directory rather than trusting an environment
# variable or a path copied from one machine.
set -u

fail() {
    echo "[worker guard] refusing to start: Worker must run in the isolated worktree:" >&2
    echo "[worker guard]   $expected_root" >&2
    echo "[worker guard] current checkout: ${current_root:-unknown}" >&2
    echo "[worker guard] current branch: ${branch:-unknown}" >&2
    echo "[worker guard] Start from .claude/worktrees/worker and branch from origin/main; do not run Worker from Brain's primary checkout." >&2
    exit 2
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
    expected_root="<unavailable>"
    current_root="unknown"
    branch="unknown"
    fail
}
current_root=$(cd "$repo_root" 2>/dev/null && pwd -P) || {
    expected_root="<unavailable>"
    branch="unknown"
    fail
}

common_dir=$(git rev-parse --git-common-dir 2>/dev/null) || {
    expected_root="<unavailable>"
    branch="unknown"
    fail
}
# Do not classify absolute-vs-relative by a leading slash. Git for Windows
# reports an absolute common dir as C:/path/..., which that test reads as
# relative; prefixing the repo root then produced a path that cannot be
# entered, so the guard refused the *correct* worktree on Windows. A relative
# common dir is relative to the current directory, which has not changed here
# (the resolutions above all run in subshells), so letting `cd` do the work
# handles the relative, POSIX-absolute and Windows-absolute forms alike.
common_dir=$(cd "$common_dir" 2>/dev/null && pwd -P) || {
    expected_root="<unavailable>"
    branch="unknown"
    fail
}
expected_root="$(cd "$common_dir/.." 2>/dev/null && pwd -P)/.claude/worktrees/worker"

branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null) || fail
case "$branch" in
    worker/*) ;;
    *) fail ;;
esac

[ "$current_root" = "$expected_root" ] || fail
exit 0
