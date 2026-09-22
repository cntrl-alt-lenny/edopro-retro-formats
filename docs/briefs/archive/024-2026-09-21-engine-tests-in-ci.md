# Active brief

Status: **accepted** (see Outcome).

Identifier: **`024-2026-09-21-engine-tests-in-ci`** — use exactly this string
as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (023 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — invariants, evidence table, and "What is
   actually enforced".
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. [`docs/engine-testing.md`](../engine-testing.md) and the module docstring of
   `tests/engine/harness.py`.
5. `.github/workflows/ci.yml`.
6. The `ignis-babelcdb`, `ignis-cardscripts` and `ygopro-core` records in
   `data/sources.json`, which pin the revisions this project claims to match.

---

## MODE: IMPLEMENTATION

## Goal

The project's duel-engine regression tests run for real in CI on every push,
against the pinned engine, card data and card scripts, and demonstrably fail
when a card behaves wrongly. Nothing that runs today becomes weaker, slower to
fail, or dependent on the network.

## Why this is next

Edison ships the modern version of 87 cards whose 2010 behaviour the project
knows differed (46 acknowledged divergences, 41 known-wrong fallbacks). The
only way to change that is roadmap item 7 — generating historical card scripts
— and the owner has chosen to start it. A generated script that nobody can
execute is not acceptable evidence, and today all 25 engine tests skip
everywhere, locally and in CI, because the engine library and the pinned
checkouts are not present. This round makes behaviour testable before any
behaviour is written.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Required investigation

1. **What engine binary, and does it match the pin?** `data/sources.json` pins
   `ygopro-core` to a specific source revision. The harness docs suggest a
   production binary from Project Ignis's DeltaBagooska. Establish whether any
   binary you use corresponds to the pinned source revision, or build from that
   revision yourself. If you cannot make the engine you run correspond to the
   pin, say exactly what it is instead and stop before recording anything as
   verified against the pin.
2. **How are BabelCDB and CardScripts obtained at exactly their pinned
   revisions**, and how does CI prove it got those revisions rather than
   whatever is current?
3. **Do the 25 tests actually pass against the pinned inputs?** Run them. Any
   that fail are findings to investigate as a regression investigation would —
   establish whether the test, the pin, or the data is wrong — not tests to
   delete, skip or loosen.
4. **Can they fail?** Demonstrate at least one engine test going red when a
   card's behaviour is deliberately wrong — for example by resolving a
   historical passcode to its modern script in a scratch copy — and green
   again when restored.

## Scope

- `.github/workflows/ci.yml` — a job, or jobs, for the engine tests.
- Any small, reviewed helper that fetches and verifies the pinned inputs.
- `docs/engine-testing.md` and the `AGENTS.md` evidence table's engine row, to
  describe what now runs where.
- Test changes only as a regression investigation justifies, each explained.

## Non-goals

- No historical card scripts, no generator, no change to errata or card data.
  That is the next round.
- No change to the main suite's standard-library-only, no-download contract:
  the existing job must keep running exactly what it runs now, with no new
  network access.
- No new workflow permissions and no CI-written branches.

## Protected invariants

- **Existing gates do not get weaker.** The current job's steps, Python
  matrix and behaviour stay as they are. A new job adds coverage; it does not
  replace or relax anything.
- **Pinned means pinned.** Every external input the engine job uses is fetched
  at a recorded revision and checked — commit hash, or a checksum for a
  binary — so a moved upstream cannot silently change what is tested. Say
  exactly how each is verified.
- **No skips in the engine job.** If the engine job runs and any engine test
  skips, the job must fail — a job that "passes" because everything skipped is
  the failure this round exists to remove. Prove this red too.
- Validator baseline 0 errors, 569 warnings; GOAT hash `0x28E9FC02`; no
  canonical data or `dist/` change.
- If a required change would alter what CI gates or need repository settings
  or permissions, stop and report; do not make it. Never bypass a check.

## Acceptance criteria

- On the pushed branch, CI runs the engine tests for real: the job's log shows
  25 executed and 0 skipped, at the exact head.
- A deliberate wrong-behaviour change makes an engine test fail (shown), and
  restoring it passes.
- A forced skip makes the engine job fail (shown).
- Every external input is pinned and verified, with the method documented.
- The existing job is unchanged in what it runs.

## Required evidence

The CI run URL and job logs at your final head; the red/green demonstrations
with real output; `python -m unittest discover -t . -s tests -v`,
`python -m retroformats validate` and `python -m retroformats build --check`
locally on Python 3.10 or newer, with real output and exit status; and, if you
can run the engine locally, that output too.

## When to stop

If the engine cannot be made to correspond to the pinned revision, or pinned
inputs cannot be verified, or a test fails for a reason you cannot establish,
stop and report with what you found rather than adjusting the pin, the test or
the data to make it pass.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/engine-tests-in-ci` from `origin/main`. Focused
commits; push the branch; never push `main`; never merge; never bypass a local
check. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from
inside `.worktrees/builder/` with
`python3 tools/report.py write --task 024-2026-09-21-engine-tests-in-ci`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus: exactly which engine binary runs and how
it relates to the pinned source revision; how each input is pinned and
verified; the CI run and counts at your head; each red/green demonstration;
and anything about the engine environment that still differs from what EDOPro
players run, stated plainly.

## Outcome — accepted 2026-09-22, merged with owner approval

Head `8a9070ebbc264bc9b4ad04a3cf0216c02c302ddd`, base
`5ab5c9d00a8bc7a6c6a8b4a3431bec8bee87ebf6`.

**Result.** A new `engine` CI job fetches BabelCDB, CardScripts and
`ygopro-core` (plus its Lua submodule) at the revisions `data/sources.json`
records, checks each by commit hash, checks premake5 by SHA-256, compiles
`ocgcore` from the pinned source, and fails if any engine test skips or fewer
than 25 run. The existing `check` job is unchanged.

**Delivery crossed machines.** The implementation was pushed from the Mac; the
owner then moved to Windows before review, and that session's report stayed in
the Mac clone's inbox. A fresh Windows Builder reviewed the inherited work,
produced the red/green demonstrations through CI with two scratch/revert
pairs on the branch (net diff zero), and wrote its own report at the new head.
The stranded report was not reconstructed. Reported upstream to the framework
through the Dev Hub.

**Brain re-derived:** ancestry; CI at the exact head (25 executed, 0 skipped,
both `check` jobs green); the red runs at the scratch commits; the workflow diff
is purely additive; the no-skip gate rejects a skip and a short count when fed
a synthetic result; validate 0 errors / 569 warnings, `build --check` clean,
full suite green locally on Windows.

**Non-blocking, carried forward:** `docs/engine-testing.md` states that the
pinned core also builds and passes on macOS arm64, with no surviving evidence
in the trail. Correct the wording, or evidence it, in a later round.
