#!/bin/sh

# Claude Code invokes this shim for hooks that must remain safe when Python is
# unavailable. Prefer python3, but retain the documented Windows/Git Bash
# fallback to python. A missing interpreter must not make a Stop hook block
# the session from ending.
set -u

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "[claude hook] no python3/python on PATH; skipping Python hook." >&2
    exit 0
fi

exec "$PYTHON" "$@"
