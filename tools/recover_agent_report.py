#!/usr/bin/env python3
"""Recover a finished agent round's final response from a provider's own
local session store, when the shared agent-inbox has nothing for it.

Absence is UNKNOWN, never "nothing happened", and a recovered message is
EVIDENCE, not ground truth: it is what the agent SAID, to be checked
against the diff, not a substitute for reviewing the diff.

Identification is by reconciliation, never "most recent conversation": a
candidate session must be tied to this repository AND corroborate the
round by branch name or exact head SHA appearing in the session. When a
commit SHA is supplied, its own commit time is the anchor: the provider
store file must still be written within the bounded post-commit window.
That excludes later sessions which merely mention an older round.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

# Fifteen minutes is an operational upper bound, not proof of authorship: it
# allows a provider to flush a finished transcript after a commit while
# excluding later rounds. Callers can tighten it with --max-lag, and the
# boundary is tested explicitly below in the repository's recovery tests.
DEFAULT_MAX_LAG = 15 * 60

def git(args, cwd=None):
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def load_config(common: Path):
    p = common / "agent-inbox" / "providers.local.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("providers", {})
    except Exception:
        return {}

def iter_jsonl(path: Path):
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
    except OSError:
        return

# ---------- provider adapters ----------

def claude_code(root: Path, glob: str, repo_paths, tokens):
    """Claude Code writes one JSONL transcript per session; every record
    carries cwd, gitBranch, sessionId and timestamp."""
    for f in sorted(root.glob(glob)):
        cwds, branches, sid, last, ts = set(), set(), None, None, None
        blob = ""
        for d in iter_jsonl(f):
            if d.get("cwd"):
                cwds.add(d["cwd"])
            if d.get("gitBranch"):
                branches.add(d["gitBranch"])
            sid = d.get("sessionId") or sid
            ts = d.get("timestamp") or ts
            if d.get("type") == "assistant":
                msg = d.get("message") or {}
                parts = [c.get("text", "") for c in msg.get("content", [])
                         if isinstance(c, dict) and c.get("type") == "text"]
                if any(p.strip() for p in parts):
                    last = "\n".join(parts).strip()
        if not (cwds & repo_paths):
            continue
        blob = " ".join(branches) + " " + " ".join(
            json.dumps(d, ensure_ascii=False) for d in iter_jsonl(f)
        )
        hits = {t for t in tokens if t in blob}
        yield {"provider": "claude-code", "file": str(f), "session": sid,
               "cwds": sorted(cwds), "branches": sorted(branches),
               "last_message": last, "mtime": f.stat().st_mtime,
               "timestamp": ts, "corroborated_by": sorted(hits)}

def codex(root: Path, glob: str, repo_paths, tokens):
    """Codex rollouts carry a purpose-built task_complete.last_agent_message.
    session_meta records only START-of-session cwd/branch, so identity must
    be corroborated from session content."""
    for f in sorted(root.glob(glob)):
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, last, ts = None, None, None
        for d in iter_jsonl(f):
            p = d.get("payload") or {}
            if d.get("type") == "session_meta":
                meta = p
            if d.get("type") == "event_msg" and p.get("type") == "task_complete":
                last = p.get("last_agent_message") or last
                ts = p.get("completed_at") or ts
        hits = {t for t in tokens if t in raw}
        yield {"provider": "codex", "file": str(f),
               "session": (meta or {}).get("id"),
               "cwds": [(meta or {}).get("cwd")] if meta else [],
               "branches": [((meta or {}).get("git") or {}).get("branch")] if meta else [],
               "last_message": last, "mtime": f.stat().st_mtime,
               "timestamp": ts, "corroborated_by": sorted(hits)}

ADAPTERS = {"claude-code": claude_code, "codex": codex}


def _candidate_is_not_primary(candidate, primary: Path) -> bool:
    """Require a recovered Worker candidate to come from a linked checkout."""
    paths = [Path(p).resolve() for p in candidate.get("cwds", []) if p]
    return bool(paths) and all(path != primary.resolve() for path in paths)


def _candidate_belongs_to_repo(candidate, repo_paths) -> bool:
    """Require provider metadata to identify one of this clone's checkouts."""
    known = {Path(path).resolve() for path in repo_paths}
    paths = {Path(path).resolve() for path in candidate.get("cwds", []) if path}
    return bool(paths & known)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--branch", help="round's worker branch, e.g. worker/adapter-hardening")
    ap.add_argument("--sha", help="round's head SHA (full or short)")
    ap.add_argument("--provider", help="restrict to one provider")
    ap.add_argument("--print-message", action="store_true")
    ap.add_argument("--max-lag", type=int, default=DEFAULT_MAX_LAG,
                    help="max seconds between the round's commit and the "
                         f"session store's last write (default {DEFAULT_MAX_LAG}; "
                         "15 minutes)")
    a = ap.parse_args()
    if a.max_lag < 0:
        ap.error("--max-lag must be non-negative")

    repo = Path(a.repo).resolve()
    common = git(["rev-parse", "--git-common-dir"], cwd=repo)
    if common is None:
        print("not a git repository", file=sys.stderr); return 2
    common = (repo / common).resolve() if not Path(common).is_absolute() else Path(common)
    primary = common.parent

    repo_paths = {str(primary)}
    for line in (git(["worktree", "list", "--porcelain"], cwd=repo) or "").splitlines():
        if line.startswith("worktree "):
            repo_paths.add(line.split(" ", 1)[1].strip())

    tokens = {t for t in (a.branch, a.sha) if t}
    if a.sha and len(a.sha) > 7:
        tokens.add(a.sha[:7])
    if not tokens:
        print("refusing to guess: pass --branch and/or --sha so the session "
              "can be reconciled to a round rather than picking the most "
              "recent conversation", file=sys.stderr)
        return 2

    commit_time = None
    commit_ref = a.sha or a.branch
    if commit_ref:
        ct = git(["show", "-s", "--format=%ct", commit_ref], cwd=repo)
        if ct and ct.isdigit():
            commit_time = int(ct)
        else:
            print(f"UNKNOWN: cannot read the commit time for {commit_ref}; "
                  "refusing to choose a session without the time anchor. "
                  "Ask for a manual relay.", file=sys.stderr)
            return 2

    cfg = load_config(common)
    if not cfg:
        print(f"no provider config at {common}/agent-inbox/providers.local.json "
              "-> UNKNOWN", file=sys.stderr)
        return 3

    cands = []
    for name, spec in cfg.items():
        if a.provider and name != a.provider:
            continue
        if spec.get("status") != "supported" or name not in ADAPTERS:
            continue
        root = Path(os.path.expanduser(spec.get("root", "")))
        if not root.is_dir():
            continue
        for c in ADAPTERS[name](root, spec.get("glob", "*.jsonl"), repo_paths, tokens):
            if (c["corroborated_by"] and c["last_message"] and
                    _candidate_belongs_to_repo(c, repo_paths) and
                    _candidate_is_not_primary(c, primary)):
                cands.append(c)

    if not cands:
        print("UNKNOWN: no session in any configured provider store could be "
              "reconciled to this round. Do not read this as 'the agent did "
              "nothing'. Ask for a manual relay.", file=sys.stderr)
        return 1

    # A session MENTIONING a SHA is not the session that PRODUCED it: a later
    # round reading `git log` corroborates every earlier round's tokens. The
    # producing session must still have been alive when the commit was made,
    # and its store file is written moments afterwards -- so anchor on the
    # commit's own time and take the nearest session that ends AFTER it.
    if commit_time is not None:
        # The producing session writes its store moments after committing.
        # A session that merely READ the SHA later (a subsequent round running
        # `git log`, or Brain's own live transcript) is excluded by this bound
        # rather than returned as a plausible-looking wrong answer.
        alive = [c for c in cands
                 if commit_time <= c["mtime"] <= commit_time + a.max_lag]
        if alive:
            cands = alive
            cands.sort(key=lambda c: c["mtime"] - commit_time)
        else:
            print(f"UNKNOWN: {len(cands)} session(s) mention this round, but "
                  f"none was still being written within {a.max_lag}s of the "
                  "commit, so none of them produced it -- they only read it. "
                  "The producing session is not in any local store on this "
                  "machine. Ask for a manual relay.", file=sys.stderr)
            return 1
        lag = cands[0]["mtime"] - commit_time
        ambiguous = [c for c in cands[1:]
                     if abs((c["mtime"] - commit_time) - lag) < 120]
    else:
        cands.sort(key=lambda c: (len(c["corroborated_by"]), c["mtime"]),
                   reverse=True)
        ambiguous = [c for c in cands[1:]
                     if len(c["corroborated_by"]) == len(cands[0]["corroborated_by"])]
    best = cands[0]
    out = {k: best[k] for k in ("provider", "session", "file", "cwds",
                                "branches", "timestamp", "corroborated_by")}
    out["candidates_considered"] = len(cands)
    out["ambiguous_with"] = [c["session"] for c in ambiguous]
    out["message_chars"] = len(best["last_message"] or "")
    if commit_time is not None:
        out["seconds_after_commit"] = int(best["mtime"] - commit_time)
    print(json.dumps(out, indent=1))
    if ambiguous:
        print("\nAMBIGUOUS: more than one session corroborates equally; "
              "reconcile by hand before trusting this.", file=sys.stderr)
    if a.print_message:
        print("\n--- recovered final response (EVIDENCE, not ground truth) ---\n")
        print(best["last_message"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
