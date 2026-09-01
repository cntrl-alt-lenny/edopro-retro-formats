# Completion-report handoff

The handoff order is deliberately provider-neutral:

1. The Worker writes its own displayed completion report with
   `python3 tools/report.py write --task <brief-identifier>`. The writer
   resolves `<git-common-dir>/agent-inbox/`, derives the role from the
   checkout, writes `<role>-latest.md`, and appends `<role>-log.md`.
2. If that artifact is absent or stale, Brain may use
   `python3 tools/recover_agent_report.py` as a provider-transcript fallback.
3. If both artifacts are unavailable, ask the owner to relay the report
   manually. Missing evidence is UNKNOWN, never proof that a round did not
   happen.

`tools/report.py status --cwd <checkout>` returns `0` for a report whose
recorded HEAD still matches, `1` for stale or unreadable provenance, and `2`
when that checkout's role has no report. The report writer's role tag is
structural: the primary checkout is `coordinator`, and a linked worktree uses
its own directory name. No role or provider name is supplied to the command.

Transcript recovery reads only provider stores configured in the untracked
`<git-common-dir>/agent-inbox/providers.local.json`. The config is machine
local and must not be copied into tracked files. Recovery requires a round
identifier (`--branch` and/or `--sha`); when a commit SHA is supplied, it
accepts only a candidate store file written from the commit time through a
15-minute upper bound. A session that merely mentions an older SHA later is
not treated as its producer. Brain's primary-checkout session is excluded
from Worker recovery, and an off-machine session is UNKNOWN unless its own
self-report was brought into the shared inbox.

Provider coverage:

| Provider | Primary path | Fallback path | If both are absent |
|---|---|---|---|
| Claude Code | Worker self-report; Stop hook is a convenience | JSONL transcript recovery | Manual relay |
| Codex | Worker self-report | JSONL rollout recovery when locally configured | Manual relay |
| Antigravity | Worker self-report; no adapter needed | Not available: its message content is in undocumented opaque SQLite blobs | Manual relay |

The Antigravity limitation applies only to transcript recovery. It does not
make the provider's normal filesystem/git/shell Worker unable to write the
canonical self-report.
