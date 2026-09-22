<!-- fw-report
round: 028-framework-3-0-0
role: builder
branch: builder/028-framework-3-0-0
head: 2ccdb4f0c729e5123aa4aadb1bca4a7f891331dc
os: macOS 27.0
python: 3.9.6
written: 2026-09-22T20:12:56Z
-->
Base: `origin/main` `eafcfda44f0f041735e123ddf3442f193d091cd0`. Head: `builder/028-framework-3-0-0` `2ccdb4f0c729e5123aa4aadb1bca4a7f891331dc`.
Python used for the suite, `validate`, `build --check` and word counts: `/opt/homebrew/bin/python3.13` (3.13.15) — this machine's `python3` is 3.9.6, below the project's 3.10 floor. `fw.py`/`adopt.py` themselves ran on that same 3.13 interpreter (they only need 3.9+).
Framework clone: `git clone --branch v3.0.0 https://github.com/cntrl-alt-lenny/agentic-framework` into a scratch folder outside and not next to this project; resolved to commit `7f5bbc3599ea01533891712f2e86d8323c8c1001` (tag `v3.0.0` is an annotated tag object over that commit — `git cat-file -p refs/tags/v3.0.0` confirmed `type commit`; the "not a commit" warning `git clone --branch` printed is a known benign quirk of resolving an annotated tag during clone, not a corruption).

## Verified

- `adopt.py <checkout> --update`, run without `--dry-run` from the framework clone — exit 0. Full output:
  ```
  update: <checkout> -> agentic-framework 3.0.0 (from 2.x (no record))
    create  docs/agents/FRAMEWORK.md
    replace docs/agents/roles/brain.md
    replace docs/agents/roles/worker.md
    replace docs/agents/roles/verifier.md
    create  tools/fw.py
    create  tests/test_framework.py
    create  docs/rounds/README.md
    beside  .claude/agents/brain.md.framework
    create  .claude/agents/verifier.md
    beside  .claude/agents/worker.md.framework
    beside  .claude/commands/status.md.framework
    remove  docs/agents/briefs.md  (unedited copy from an earlier release)
    remove  docs/agents/kickoff.md  (unedited copy from an earlier release)
    remove  docs/agents/lifecycle.md  (unedited copy from an earlier release)
    remove  tests/test_role_neutrality.py  (unedited copy from an earlier release)
    remove  tools/authority.py  (unedited copy from an earlier release)
    remove  tools/neutrality.py  (unedited copy from an earlier release)
    remove  tools/textblocks.py  (unedited copy from an earlier release)
    keep    AGENTS.md, docs/state.md, .gitattributes, .githooks/pre-push, CLAUDE.md  (project-owned)
    keep    .claude/hooks/run_python.sh, .claude/hooks/save_agent_reply.py, .claude/settings.json,
            tests/test_report.py, tools/report.py  (edited in this project, so kept; delete once nothing needs it)
    keep    docs/agents/reports.md, roles/README.md, state.md, adapters.md, git-and-isolation.md,
            evidence.md, topologies.md, docs/agents/CONSTITUTION.md  (still referenced; remove the
            reference, then delete)
    record  docs/agents/framework.json

  fix this link after the update: AGENTS.md links to docs/agents/kickoff.md
  fix this link after the update: AGENTS.md links to docs/agents/lifecycle.md

  [+ the 3.0.0 "What an adopter must do" steps printed verbatim, and the pre-manual-work
   `fw.py check` findings: docs/state.md 3620 words over its 1000 budget; no Merge rule: line;
   AGENTS.md 2826 words; a Windows drive path at docs/state.md:193]
  ```
  This matches Brain's dry-run prediction in the brief exactly (files created/replaced/beside/removed,
  the two flagged links, the "still referenced" keeps). Committed as `8005dcb`.

- Every leftover-inventory row (1-18) decided and actioned — see **Changed** for the per-row disposition; every default recommendation was followed except none needed overriding.

- `adopt.py <checkout> --update --dry-run` at the final head — exit 0, plans nothing:
  ```
  update: <checkout> -> agentic-framework 3.0.0 (from 3.0.0)
    same    docs/agents/FRAMEWORK.md
    same    docs/agents/roles/brain.md
    same    docs/agents/roles/worker.md
    same    docs/agents/roles/verifier.md
    same    tools/fw.py
    same    tests/test_framework.py
    same    docs/rounds/README.md
    same    .claude/agents/brain.md
    same    .claude/agents/verifier.md
    same    .claude/agents/worker.md
    same    .claude/commands/status.md
    keep    AGENTS.md, docs/state.md, .gitattributes, .githooks/pre-push, CLAUDE.md  (project-owned)
    record  docs/agents/framework.json

  dry run: nothing written
  ```
  No `create`, `replace`, `beside` or `remove`; no "delete it" keeps; no link-fix notes. Meets acceptance criterion 2.

- `fw.py --cwd <checkout> status` — exit 0:
  ```
  Framework
    pinned to agentic-framework 3.0.0 (https://github.com/cntrl-alt-lenny/agentic-framework)
    up to date with the latest release (3.0.0)
  Merge rule
    owner-approves
  Rounds
    in flight: 028-framework-3-0-0 -- brief on origin/brain/028-framework-3-0-0 (+2 more)
    legacy docs/briefs/active.md present -- from before release 3.0.0; new rounds use docs/rounds/
  Checks
    all project checks pass
  ```
  3.0.0 pinned, no locally-edited framework files reported, only legacy note is `docs/briefs/active.md`. Meets acceptance criterion 3.

- `fw.py --cwd <checkout> check` — exit 0: `0 error(s), 0 warning(s)`. Meets acceptance criterion 4.

- `python -m unittest discover -t . -s tests -v` (3.13.15) — exit 0: `Ran 996 tests ... OK (skipped=25)`. Baseline at `main` `eafcfda` (re-run in a temporary detached worktree at that commit, same interpreter): `Ran 1067 tests ... OK (skipped=25)`. Skip count unchanged (still only the engine tests needing `ocgcore`/pinned checkouts). Net -71 tests, fully reconciled against the inventory (counted `    def test_` per file at `eafcfda` vs. head):
  - `tests/test_role_neutrality.py`: -10 (item 1: unedited 2.x copy, removed by `adopt.py`; 3.0.0 drops the wording scanners it tested).
  - `tests/test_report.py`: -29, `tests/test_report_delivery.py`: -6, `tests/test_report_recovery.py`: -6 (item 7/8: the report-inbox mechanism and its tools are retired).
  - `tests/test_claude_adapter.py`: -16 (item 9: Stop-hook/shim/checkout-guard tests and their subjects deleted; its one surviving test, `TrackedHookModeTest`, is not lost — it is the `+1` in `tests/test_push_readiness.py` below).
  - `tests/test_state_doc_is_durable.py`: 7 -> 1, -6 (item 10: kept only the live-queue-phrase check `fw.py check` doesn't cover).
  - `tests/test_framework.py`: +1 (new, installed by `adopt.py`).
  - `tests/test_push_readiness.py`: +1 (`TrackedHookModeTest`, moved in from `test_claude_adapter.py`).
  - Sum: -10-29-6-6-16-6+1+1 = -71. `1067-71 = 996`, matching the observed count exactly. Meets acceptance criterion 5 (every removed test accounted for).

- `python -m retroformats validate` (3.13.15) at head — exit 0: `3 formats, 3 banlists, 3 pools, 3 rule profiles, 296 errata -> 0 errors, 569 warnings`. Re-run identically at `main` `eafcfda` in a temporary detached worktree: same `0 errors, 569 warnings`. GOAT hash and banlist entry sets: unaffected — this round touched no file under `data/`, `formats/`, `dist/`, `schemas/`, `retroformats/` or `scripts/` (other than the two docstring/comment edits named in scope), confirmed by the `git diff --stat` below.

- `python -m retroformats build --check` (3.13.15) — exit 0 at head and (separately) at `main` `eafcfda`, both: `built 2005-04-goat/2010-03-edison/2011-09-tengu -> dist/lflists/*.lflist.conf` with no drift reported. Meets acceptance criterion 6.

- `git diff --stat origin/main...HEAD` — 55 files changed, 2352 insertions(+), 7563 deletions(-). Every path is inside the brief's "May change" scope (`.claude/**`, `.githooks/pre-push`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `docs/agents/**`, `docs/archive/**`, `docs/briefs/README.md`, `docs/briefs/delivered/.gitkeep`, `docs/rounds/**`, `docs/state.md`, `scripts/check_push_readiness.py`, `tests/test_*` named in the inventory, `tools/*`); nothing under `data/`, `formats/`, `dist/`, `schemas/`, `retroformats/`, `docs/research/`, product tests or `.github/workflows/` was touched.

- The brief's leftover grep, run at head — one hit, in a framework file this round must not hand-edit:
  ```
  tools/fw.py:693:        if (root / "docs/agents/CONSTITUTION.md").is_file():
  ```
  This is `fw.py`'s own 2.x-detection heuristic (`framework_lines`): when a project has no `docs/agents/framework.json` manifest at all, it checks whether `docs/agents/CONSTITUTION.md` exists to report "2.x framework layout, plan an update round" instead of "not adopted, or damaged". It is functional framework code, not a stale project cross-reference — this project now has `docs/agents/framework.json`, so that branch is never reached for it, and the file no longer exists in this checkout anyway. `tools/fw.py` is explicitly out of scope to hand-edit (brief § Scope and non-goals; `FRAMEWORK.md` rule 14). Every other match the grep would have flagged (project docs, `.claude/`, other `tools/`) is clean. I did not file a framework-feedback issue for this — it is accurate, working code, not a defect — but it is worth Brain/the framework's own maintainers knowing the heuristic's name will look odd in a `git grep` sweep like the one this brief specifies; noted here rather than worked around.

- `AGENTS.md`: 2299 words (budget 2500). `docs/state.md`: 998 words (budget 1000, i.e. `fw.py check`'s `words(text) > budget` does not fire). Meets acceptance criterion 9.

- CI at the pushed head `2ccdb4f0c729e5123aa4aadb1bca4a7f891331dc` (run `35778461589`, https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/35778461589) — conclusion `success`, all three jobs green: `engine` (1m11s), `check (3.10)` (42s), `check (3.13)` (24s). Meets acceptance criterion 11.

- Windows rename-retry exposure (item 7's specific ask): established that `fw.py`'s `cmd_report` (the 3.0.0 replacement for `tools/report.py write`) writes each round's report with a single `path.write_bytes(header + body)` directly to `docs/rounds/<id>/<role>.md`, then `git add`/`git commit`s that same file. There is no `os.replace` onto a path another process has open (grepped `tools/fw.py` for `os.replace`/`WinError`/`retry`: no matches), and nothing polls that path concurrently the way the old `.git/agent-inbox/<role>-latest.md` was polled by `report.py status` from a second process while a Stop hook or another role's session might be writing it. The specific Windows failure this project's `tools/report.py` worked around (`PermissionError [WinError 32]` from `os.replace` racing a concurrent reader) does not carry over to `fw.py report`. Recorded in `docs/archive/state-history.md` under "The Claude adapter's demonstrated defect classes" alongside the verbatim history it follows from.

## Not verified

- Whether CI's Windows runners would reproduce anything — this project's CI only runs `ubuntu-latest` (`check` job twice, `engine` job once); there is no Windows CI job to check, consistent with `AGENTS.md`/`docs/state.md`'s existing statement that the duel engine builds on Linux/macOS only and Windows engine evidence comes from CI (which itself doesn't run Windows). Not something this round could change or needed to.
- Whether the owner's other machine (Windows desktop, per `docs/archive/state-history.md`'s Dev Hub section) has `core.hooksPath` configured, or any other per-machine fact — out of scope by design; `docs/state.md` deliberately stores none of that.
- `docs/agents/framework.json`'s recorded sha256 hashes against a byte-for-byte re-hash — trusted `adopt.py`'s own `record` step rather than independently recomputing every hash; `fw.py check`/`status` both read that same file and reported clean, which is the mechanism's own self-check.
- The framework repository's own test suite, or anything about the framework beyond what `v3.0.0`'s tag, `CHANGELOG.md`, `FRAMEWORK.md` and the role cards say — out of scope for this project's round.

## Changed

Leftover inventory, one line each (default recommendation followed in every row; no overrides):

1. `docs/agents/briefs.md`, `kickoff.md`, `lifecycle.md`; `tools/authority.py`, `neutrality.py`, `textblocks.py`; `tests/test_role_neutrality.py` — removed by `adopt.py` (unedited 2.x copies; 3.0.0 drops the wording scanners).
2. `docs/agents/CONSTITUTION.md`, `adapters.md`, `evidence.md`, `git-and-isolation.md`, `reports.md`, `state.md`, `topologies.md`, `roles/README.md` — deleted. No project-specific content found in any of the eight beyond what `AGENTS.md`'s existing Topology/Authority sections and the framework's own `FRAMEWORK.md`/role cards already state; nothing needed moving.
3. `docs/agents/model-notes.md` — deleted; it is a dated round-by-round log (rounds 1-23), not a standing rule — confirmed by reading the whole file; git history keeps it. `docs/agents/push-gate.md` — deleted; its pre-push facts (runs `validate`+`build --check`, opt-in per clone via `core.hooksPath`, `--no-verify` bypass, lives at git's pre-push layer rather than a tool hook and why) folded into `AGENTS.md` § What is actually enforced's pre-push row. Its more detailed "scope limitations" (checks the current checkout only; `build --check` silently overwrites an *uncommitted* `dist/` hand-edit rather than reporting it) were **not** carried into `AGENTS.md` to stay inside the "a line or two" the brief asked for — flagged under Open questions. `docs/agents/report-handoff.md` — deleted; it describes the retired report-inbox fallback chain (self-report / transcript recovery / owner relay) wholesale, superseded by `fw.py report`/`delivery`; moved verbatim to `docs/archive/state-history.md`.
4. `.claude/agents/brain.md`, `worker.md`, `.claude/commands/status.md` — replaced with their `.framework` copies, then the `.framework` files removed. Dropped: `model: sonnet` pins (tool configuration; the owner picks models per session — this was already true, not a new decision, so recorded here rather than restated as an AGENTS.md rule); the Ultracode note (Claude-Code-specific, not a project rule); the `core.hooksPath` check (folded into `AGENTS.md`, see row 3); the checkout-guard hook (see row 5); `worker.md`'s old "read `docs/briefs/active.md` unless pointed elsewhere" (obsolete — briefs now live in `docs/rounds/`) and its "start in fresh context" line (redundant with the 3.0.0 `worker.md` card's own "read what the brief points to; do not read the whole repository 'to be safe'"); `status.md`'s old nine-step manual rehydration checklist (superseded by `fw.py status`, which now does that derivation itself).
5. `.claude/hooks/check_worker_checkout.sh` — deleted (contradicts 3.0.0 seats working from any checkout).
6. `.claude/settings.json`, `.claude/hooks/run_python.sh`, `.claude/hooks/save_agent_reply.py` — deleted (Stop hook retired; seats commit their own reports now).
7. `tools/report.py`, `tools/recover_agent_report.py` — deleted, replaced by `fw.py report`/`delivery`. Windows rename-retry exposure: established not to carry over — see **Verified**.
8. `tests/test_report.py`, `test_report_delivery.py`, `test_report_recovery.py` — deleted with their subjects.
9. `tests/test_claude_adapter.py` — Stop-hook/shim/checkout-guard tests and subjects deleted; its `TrackedHookModeTest` (the pre-push executable-bit test) moved into `tests/test_push_readiness.py`.
10. `tests/test_state_doc_is_durable.py` — kept only `test_makes_no_live_queue_claim`; dropped the git-SHA-pin check, the per-machine-setup-phrase check, the `docs/briefs/active.md`-dependent check and the whole `FrameworkDocsAreDurableTest` class (SHA pins and machine-setup phrasing across `docs/agents/`) — all now covered by `tests/test_framework.py` via `fw.py check`'s `check_project`, confirmed by reading its source (`PERSONAL` patterns cover Windows/macOS/Linux paths and email addresses over `AGENTS.md`, `CLAUDE.md`, `docs/state.md` and everything under `docs/agents/`+`docs/rounds/`; `SHA40` covers stored 40-hex commit ids outside `## Historical anchors`).
11. `tests/test_push_readiness.py` — kept; `test_hook_is_not_wired_as_a_claude_code_bash_hook` now asserts the invariant explicitly (no Bash push hook) instead of skipping when `.claude/settings.json` is absent, which it now always is.
12. `.githooks/pre-push`, `scripts/check_push_readiness.py` — kept; repointed their `docs/agents/push-gate.md` comment/docstring references to `AGENTS.md § What is actually enforced` (comment-only, behaviour unchanged).
13. `.gitignore` — kept `.worktrees/`; dropped the `.claude/worktrees/` pre-adoption entry and its comment's link to the now-deleted `git-and-isolation.md`.
14. `docs/archive/agents-pre-framework/` — deleted (`README.md`, `role-contracts.md`, `worktree-mechanism.md`), along with `AGENTS.md`'s pointer to it. Confirmed by reading all three that nothing there was still-normative (each already carried a "RETIRED 2026-09-16 — history, not policy" banner).
15. `docs/briefs/README.md` — kept as history, with a new line at the top pointing new rounds at `docs/rounds/`. `docs/briefs/delivered/.gitkeep` — deleted (the "delivered" stage no longer exists).
16. `docs/briefs/active.md` — untouched, as instructed (Brain retires it when it re-issues round 027).
17. `.claude/commands/atlas.md`, `report.md` — kept; read both in full, neither references anything retired by this round.
18. `CLAUDE.md` — replaced with the framework's exact pointer (`@AGENTS.md` plus its one sentence).

`AGENTS.md` — rewritten as the single entry point: `Merge rule: owner-approves` line added; points at `docs/agents/FRAMEWORK.md` and the role cards; states seats work from any checkout via `fw.py start` and that `.worktrees/<role>/` is an optional convenience; states the Verifier commits only its report, on its own branch; states framework feedback goes to the framework repository's GitHub issue form; carries every project rule this round could locate (see the accounting table below); drops the restated authority model/round lifecycle/brief-identifier text/`report.py` mechanics/checkout mechanics, the Claude-executor-guard enforcement row, links to now-deleted files, and the Dev Hub. Final word count 2299, under the 2500 budget.

`docs/state.md` — trimmed from 3620 to 998 words. Sentence-level accounting (sections moved **verbatim** are listed by heading; everything else was reworded/condensed, which the word-count drop from 3620 to 998 already demonstrates and which is not practical to list sentence-by-sentence for prose that was rewritten rather than removed):

- **Moved verbatim to `docs/archive/state-history.md`** (confirm with `git diff --stat` against `eafcfda` on `docs/archive/state-history.md` vs. the corresponding headings removed from `docs/state.md`): "Owner decision — merges need explicit owner approval (since 2026-09-16)" (full section); "Dev Hub and framework feedback (since 2026-09-22)" (full section, replaced in `docs/state.md` by a two-line pointer: the merge-approval section now just points at `AGENTS.md`'s merge rule, and framework feedback now goes to GitHub issues); the four bullets under the old "Open items and sequencing judgements" heading describing 2.x mechanism history — "The Claude adapter has four demonstrated defect classes..." (plus its two follow-up bullets on the worktree-fixture rule and the Windows `git-common-dir` bug), "`report.py`'s atomic write loses to a concurrent reader on Windows...", "`tools/report.py` is deliberately not byte-identical to the framework's copy...", "A round's completion report reaches Brain by a provider-neutral self-report first..." (plus its "transcript-recovery fallback over-rejects" and "Claude Stop hook is fallback-only" follow-ups), and "The adoption itself was owner-commissioned Brain work, not a reviewed round..."; and the old "## Review protocol" section (also moved, though the brief did not name it explicitly — it restates `FRAMEWORK.md` rules 7/9/10 and `AGENTS.md` § What review checks here almost verbatim, so treated the same as the other 2.x restatements rather than kept twice).
- **Kept, condensed:** the live-state derivation table (its "round in flight" row now points at `fw.py status`/`docs/rounds/` instead of `docs/briefs/active.md`+`delivered/`; its "past rounds" row drops the now-deleted `model-notes.md` link); Architecture invariants (all eight rulings kept, wording tightened); Canonical formats table and both formats bullets; Tokyo Dome (condensed — see Open questions for what was cut); Erratum v2; the standing-role-chats decision; the operating-policy standing rules (all seven bullets kept, tightened); the sequencing judgements (all seven kept, tightened; see Open questions for the one bullet trimmed); owner preferences (all four kept). New `## Historical anchors` section: GOAT hash, Tokyo Dome certified-pool digest, Erratum v2 corpus size, the Linux/macOS-only engine fact — all four are values FRAMEWORK.md § State says belong under that heading.

New file `docs/archive/state-history.md` — created, holding the verbatim-moved sections above under their original headings, each followed by a one-line note pointing at the current 3.0.0 mechanism that superseded it.

## Open questions

- **The adopt.py leftover-grep false positive on `tools/fw.py:693`** (see Verified) is accurate framework behaviour, not a defect — noted rather than worked around, per the brief's "don't work around a framework problem silently" instruction. I judged it below the bar for a framework-feedback issue (it's correct code, not a bug); Brain or the owner may disagree.
- **Two deliberate trims below "keep in substance"**, both to fit `docs/state.md`'s 1000-word budget: (1) the daiti0526-photograph sentence in the Tokyo Dome paragraph (that the photos authenticate only a parallel Game Boy tournament's date/venue, never the restriction list itself) is dropped — the paragraph still says the restriction-list evidence is tier C/unauthenticated, just without that specific second-source distinction; (2) the "Roadmap 1a is large and open-ended, prefer better-bounded items" sequencing judgement is dropped entirely rather than condensed — `docs/roadmap.md` is stated as canonical for what's open and likely still carries item 1a's own description. If either of these turns out to be load-bearing, they're recoverable verbatim from `main` `eafcfda`'s `docs/state.md`.
- **`docs/agents/push-gate.md`'s "scope limitations" were not carried into `AGENTS.md`** (see Changed, row 3) — specifically that `build --check` regenerates `dist/` before comparing, so it silently overwrites an uncommitted hand-edit rather than reporting it. This is a real, slightly sharp edge (a Builder could believe an uncommitted `dist/` change was checked when it was actually discarded) that no longer has a home in any tracked document. Judged out of the "a line or two" the brief asked for; flagging in case Brain judges it worth a sentence somewhere.
- **This project's `MODE:`/mode vocabulary is now entirely project-owned**, not partly framework-defined. The 2.x `docs/agents/roles/worker.md` had a full "Modes" section (IMPLEMENTATION, RESEARCH, SOURCE VERIFICATION, ADVERSARIAL AUDIT, DATA/SCHEMA, REGRESSION INVESTIGATION, DOCUMENTATION) that the 3.0.0 `worker.md` card dropped entirely — the only surviving trace of a mode vocabulary in the framework is `docs/agents/roles/brain.md`'s brief-template line, `Mode: <implementation | research | investigation | data | documentation | audit>`. `AGENTS.md`'s "Modes this project uses" section now maps `HISTORICAL RESEARCH` onto `research` and states `audit` is the Verifier's, using that six-word vocabulary — but per-mode behavioural rules (e.g. "an investigation-mode brief must establish which of two things is wrong before changing either") are no longer backed by any framework text at all, only by this project's own `AGENTS.md`. This is a genuine, load-bearing change in what the framework provides, not a wording choice on my part — worth Brain/the owner knowing explicitly, since a future brief writer might assume "research mode" still means what the 2.x contract spelled out.
- Whether the owner wants `AGENTS.md`'s two `model: sonnet` pins (dropped from `.claude/agents/brain.md` and `worker.md`) replaced with something, or whether "the owner picks models per session" needs stating anywhere machine-readable — treated as already-true prior practice needing no new rule, per the brief's "drop them and record that" instruction; recorded here rather than invented as a new `AGENTS.md` line.
