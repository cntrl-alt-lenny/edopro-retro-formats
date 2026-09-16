# Completion reports — this project's recovery fallback

The mechanism itself is canonical and lives in [`reports.md`](reports.md): every
Builder and Verifier writes its own report with
`python3 tools/report.py write --task <brief identifier>` before ending its
turn, and a missing or stale report means UNKNOWN. This file adds only what is
specific to this repository: a second fallback that sits between "check the
shared inbox" and "ask the owner to paste it".

## Fallback order here

1. The role's own self-report in `<git-common-dir>/agent-inbox/<role>-latest.md`
   (see `reports.md`). Check freshness with
   `python3 tools/report.py status --cwd .worktrees/<role>`.
2. **Only if that is absent or stale:** `python3 tools/recover_agent_report.py`,
   which searches locally configured provider transcript stores.
3. If both are unavailable, ask the owner to relay the report. Missing evidence
   is UNKNOWN, never proof that a round did not happen.

## Transcript recovery

Recovery reads only provider stores configured in the untracked
`<git-common-dir>/agent-inbox/providers.local.json`. The config is machine local
and must not be copied into tracked files. Recovery requires a round identifier
(`--branch` and/or `--sha`); when a commit SHA is supplied, it accepts only a
candidate store file written from the commit time through a 15-minute upper
bound. A session that merely mentions an older SHA later is not treated as its
producer. The coordinating session's primary checkout is excluded, and an
off-machine session is UNKNOWN unless its own self-report was brought into the
shared inbox.

**Known defect, fails closed:** the primary-checkout exclusion rejects any
session that *ever* recorded the primary checkout as a working directory, which
real producing sessions routinely do. Recovery therefore returns UNKNOWN for
some genuine rounds. It never returns a wrong answer, and the self-report in
step 1 is unaffected. See `docs/state.md` for the intended fix.

Provider coverage for the recovery fallback only — every provider's executor can
still write the step-1 self-report, because that needs nothing but a shell and
git:

| Provider store | Recovery fallback |
|---|---|
| Claude Code JSONL transcripts | Supported |
| Codex JSONL rollouts | Supported when locally configured |
| Antigravity | Not available: message content is in undocumented opaque SQLite blobs |
