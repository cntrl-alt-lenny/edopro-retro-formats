# Push-readiness gate

Before a push reaches the remote, this repository can run the same two
data/build checks CI runs:

```
python -m retroformats validate
python -m retroformats build --check
```

The point is early feedback — catching validator errors or `dist/` drift
while the failing output is still in front of whoever caused it, instead
of finding out from a CI run several steps later.

## Activate it (per clone, including on a fresh clone)

```bash
git config core.hooksPath .githooks
```

This is **not** automatic. A fresh clone has no hook until this is run.
There is no way to make a repository configure its own hooks on clone —
that is a deliberate Git security property, not an oversight to work
around. The tracked `.githooks/pre-push` file also carries executable mode;
if a local filesystem strips that mode, restore it with
`chmod +x .githooks/pre-push`.

Bypass a single push with `git push --no-verify`. That skips the local
hook only; it does not skip CI.

## What it is, and what it is not

**It is a convenience, not a control.** Specifically:

- it is opt-in per clone, so it may simply not exist wherever a given push
  comes from;
- `--no-verify` bypasses it by design;
- there is **no server-side enforcement behind it**. This repository has
  no pre-receive hook or protected-branch check; nothing on the remote
  re-runs these checks at push time.

**[CI](../../.github/workflows/ci.yml) is the only backstop that always
runs** — it executes both of these commands plus the full test suite on
every push and pull request. Treat a green local hook as "I probably
didn't just waste a CI round", never as "this is enforced."

## How it is put together

| file | role |
|---|---|
| `.githooks/pre-push` | thin shell shim; resolves `python3` or `python` and execs the script |
| `scripts/check_push_readiness.py` | all the logic, plus the rationale and limits in its docstring |
| `tests/test_push_readiness.py` | unit tests for the logic and the shim, run by the normal suite |

The split exists so the logic is testable — a check living entirely inside
a shell hook could not be exercised by `python -m unittest`.

## Why it lives at Git's pre-push layer

An earlier version was a Claude Code `PreToolUse` hook that recognised a
push by regex over the Bash command text. That layer was wrong for two
independent reasons, both verified against the real implementation before
it was replaced (and now pinned by
`tests/test_push_readiness.py::CommandTextParsingRegressionTest`):

1. **It missed ordinary pushes** — `git -C <path> push`, `sh -c "git
   push"`, `bash -c "..."`, `(git push)`, `$(git push)`, and `git.exe
   push` all slipped through.
2. **It blocked things that were not pushes** — any Bash command merely
   containing the phrase, including `git commit -m "docs: explain the git
   push flow"`, which is exactly the kind of commit message this project
   writes.

At the pre-push layer there is no command text to parse: Git has already
decided a push is happening. It is also **vendor-independent**, which
matters more here than the parsing bugs — this project's Worker role is
explicitly model-agnostic (`AGENTS.md`), and a Claude Code hook never
fired at all for a Worker round run through another vendor's tool. A Git
hook fires for every client: any agent tool, a plain terminal, an IDE.

## Scope limitations

Both verified by deliberately breaking things and watching what the gate
did and did not catch:

- It validates the **current checkout** at push time, not each pushed
  commit individually.
- `build --check` **regenerates `dist/` before comparing**, so an
  *uncommitted* hand-edit to `dist/` is silently overwritten rather than
  reported. What it does catch is committed `dist/` content that
  disagrees with what canonical data generates — which is the case that
  actually matters.
