<!-- fw-report
round: 028-framework-3-0-0
role: verifier
branch: verifier/028-framework-3-0-0
head: 06d3ba3f49cbb204f84fbddf144567a03c21c231
os: macOS 27.0
python: 3.13.15
written: 2026-09-22T20:32:19Z
-->
Reviewed commit: `06d3ba3f49cbb204f84fbddf144567a03c21c231` (branch
`origin/builder/028-framework-3-0-0`, as pinned by `fw.py start`). Base:
`origin/main` `eafcfda44f0f041735e123ddf3442f193d091cd0`.

Commands I ran myself, from my own checkout (`.worktrees/verifier`, on
`verifier/028-framework-3-0-0`), framework cloned fresh at tag `v3.0.0`
(resolved `7f5bbc3599ea01533891712f2e86d8323c8c1001`) into a scratch folder
outside and not next to this project. `python3` on this machine is 3.9.6,
below the project's 3.10 floor, so the suite/validate/build/word-count
commands used `/opt/homebrew/bin/python3.13` (3.13.15); `fw.py`/`adopt.py`
themselves ran on the same interpreter (they only need 3.9+):

- `git clone --branch v3.0.0 …/agentic-framework` — exit 0. The clone printed
  `warning: refs/tags/v3.0.0 … is not a commit!`; checked it myself:
  `git cat-file -t <tag-sha>` → `tag`; `git cat-file -p <tag-sha>` shows a
  proper annotated tag object (`type commit`, tagger the owner's own GitHub
  identity) over commit `7f5bbc35…`, which matches `CHANGELOG.md`'s 3.0.0
  section and `git describe --tags` → `v3.0.0`. Benign quirk of resolving an
  annotated tag mid-clone, not corruption — agrees with the Builder's report.
- `git worktree add --detach .worktrees/verifier origin/main` — exit 0.
- `python3 <framework>/tools/fw.py --cwd <checkout> start --role verifier --round 028-framework-3-0-0` — exit 0, pinned me to the commit above.
- `python3 <framework>/tools/adopt.py <checkout> --update --dry-run` — exit 0, plans nothing (`same`/`keep`/`record` only, no `create`/`replace`/`beside`/`remove`, no link fixes). Meets acceptance criterion 2.
- `python3 <framework>/tools/fw.py --cwd <checkout> status` — exit 0: 3.0.0 pinned and up to date, `Merge rule: owner-approves`, only legacy note `docs/briefs/active.md`, all project checks pass. Meets acceptance criterion 3.
- `python3 <framework>/tools/fw.py --cwd <checkout> check` — exit 0: `0 error(s), 0 warning(s)`. Meets acceptance criterion 4.
- `python -m unittest discover -t . -s tests -v` (3.13.15) — exit 0: `Ran 996 tests … OK (skipped=25)`. Same skip count as the brief's baseline (1067, skipped=25). I independently counted `def test_` per changed file at `eafcfda` vs. head and reconciled the same way the Builder's report does: `-10` (`test_role_neutrality.py`) `-29/-6/-6` (`test_report.py`/`_delivery`/`_recovery`) `-16` (`test_claude_adapter.py`, its one surviving test moving to `test_push_readiness.py`, `+1` there) `-6` (`test_state_doc_is_durable.py`, 7→1) `+1` (new `test_framework.py`) = net `-71`; `1067-71=996`. Exact match. Meets acceptance criterion 5.
- `python -m retroformats validate` at head and, separately, at `origin/main` — both exit 0, both `3 formats, 3 banlists, 3 pools, 3 rule profiles, 296 errata -> 0 errors, 569 warnings`, byte-identical output (`diff` confirmed). No product path is touched by `git diff --stat origin/main...HEAD -- data/ formats/ dist/ schemas/ retroformats/ docs/research/ .github/workflows/` (empty).
- `python -m retroformats build --check` at head and at `origin/main` — both exit 0, both build the same three lflists with no drift reported. Meets acceptance criterion 6.
- `git diff --stat origin/main...HEAD` — 56 files changed, 2519 insertions(+), 7563 deletions(-) (one file and 167 lines more than the Builder's own citation of 55/2352, because my head includes the report commit itself, `docs/rounds/028-framework-3-0-0/builder.md`, which the Builder's figure was taken before). Every changed path is inside the brief's "May change" list; nothing outside it.
- The brief's leftover grep, run verbatim — one hit: `tools/fw.py:693: if (root / "docs/agents/CONSTITUTION.md").is_file():`. Read the surrounding function (`framework_lines`): it is the tool's own legacy-layout detector, used only when a project has no `docs/agents/framework.json` at all. Confirmed the installed `tools/fw.py` is byte-identical to the framework clone's copy (`diff` — identical), so this is inherited framework code the Builder is barred from hand-editing, not a leftover reference. Agrees with the Builder's report and its choice not to file a framework-feedback issue over it.
- Word counts: `AGENTS.md` 2299 words (< 2500), `docs/state.md` 998 words (≤ 1000). Meets acceptance criterion 9.
- `gh api repos/cntrl-alt-lenny/edopro-retro-formats/commits/06d3ba3.../check-runs` — `check (3.13)`, `check (3.10)`, `engine` all `completed`/`success`, at the exact reviewed commit. Meets acceptance criterion 11.
- Spot-checked the "moved verbatim" claim for one archive section: diffed the "Owner decision — merges need explicit owner approval" text between `origin/main`'s `docs/state.md` and `docs/archive/state-history.md`. Identical apart from a two-line pointer note appended at the end, as the report describes.
- Grepped all eight files in leftover-inventory row 2 (`CONSTITUTION.md`, `adapters.md`, `evidence.md`, `git-and-isolation.md`, `reports.md`, `docs/agents/state.md`, `topologies.md`, `roles/README.md`) at `origin/main` for project-specific terms (`goat`, `edison`, `tengu`, `errata`, `legality_basis`, `reserved-passcode`, `retroformats`, `edopro`, the GOAT hash) — no hits in any of them, supporting the report's claim that none needed project-specific content moved into `AGENTS.md`.
- Read `docs/agents/model-notes.md` at `origin/main` in full: one `## Round log` heading, everything else dated round entries — supports deleting it as a log, not a standing rule.
- Grepped `tools/fw.py` for `os.replace`/`WinError`/`retry` (none) and read `cmd_report`: it writes each report with a single `path.write_bytes(...)` and then `git add`/`git commit`s the same path — no atomic-replace race with a concurrent reader, unlike the retired `report.py` inbox file. Independently confirms the report's Windows-rename-retry finding for item 7.

## Findings

- [SHOULD FIX] `docs/rounds/028-framework-3-0-0/builder.md:136` — the accounting for the dropped `.claude/agents/worker.md` line "Start in fresh context. A session carrying Brain's reasoning about the brief is no longer independent" calls it "redundant with the 3.0.0 `worker.md` card's own 'read what the brief points to; do not read the whole repository "to be safe"'". I read `<framework>/framework/roles/worker.md` in full myself: that quoted sentence is step 2 of Start, and its subject is not re-reading the repository beyond what the brief points to — it says nothing about a Worker session inheriting Brain's own reasoning about the brief, which is what the dropped line protected against. The two are not the same concern, so the stated reason is inaccurate, and acceptance criterion 10 requires an accurate reason for every dropped rule. It fails silently rather than loudly: nothing in the new `AGENTS.md` or the role cards states the Worker-independence concern, so a future reader has no way to learn it was ever a rule, or that it is still being handled. In practice the underlying concern is not actually unprotected — `docs/state.md`'s pre-existing "Owner decision — standing role chats" section (untouched in substance by this round) already names it explicitly ("overriding the framework's fresh-context preference in those two cases only") and is the real place this project tracks it, via `FRAMEWORK.md` rule 2 ("Git is the only memory") and the round design's self-contained prompts. I'd fix the accounting line to cite that anchor instead of the worker.md quote, rather than leave the drop looking like something the framework now covers on its own.

## Not verified

- I did not re-hash `docs/agents/framework.json`'s recorded SHA-256 values byte-for-byte; I relied on `adopt.py --update --dry-run` reporting every copy file `same` and `fw.py check` reporting clean, the same self-check the Builder's report relies on.
- I did not read every sentence of the reworded (non-verbatim) portions of `docs/state.md` against the 3620-word original line by line — I spot-checked one verbatim-moved section (identical) and skimmed the rest; for prose that was genuinely reworded rather than removed, sentence-level diffing isn't practical, which the report itself says.
- I have no Windows machine to reproduce anything on; I relied on reading `cmd_report`'s source rather than executing it under Windows. This project's CI has no Windows job either, so this is consistent with everything else in the repository.
- Framework-internal behavior beyond what `v3.0.0`'s tag, `CHANGELOG.md`, `FRAMEWORK.md` and the role cards state is out of scope, same as the Builder's report says.
- Methodology note, for transparency: during my first pass, before reading the Builder's report, a `git grep` I ran across the working tree (to check whether a project rule survived anywhere) did not exclude `docs/rounds/028-framework-3-0-0/builder.md`, and one line of that report's own text appeared in the match output. I did not treat it as established and instead re-derived the underlying claim myself from the framework's actual `worker.md` card before forming the finding above — the finding stands on that independent re-derivation, not on the glimpsed line. I could not fully undo having seen it, so I'm disclosing it per the contract's independence requirement rather than treating my pass as unaffected by default.

## Verdict

I believe this round does what it says: the project runs cleanly on agentic-framework 3.0.0 with no half-state. Every command the brief and the framework require gives the exact result both the brief's baseline and the Builder's report claim — `adopt.py --update --dry-run` plans nothing, `fw.py status`/`check` are clean, the suite is green at 996 tests with the net -71 fully reconciled against the leftover inventory, `validate`/`build --check` are byte-identical to `main` (no product path touched, GOAT hash therefore unmoved), word budgets are met, and CI is green on all three jobs at the exact reviewed commit. All 18 inventory rows were actioned as recommended, and I could find no project-specific content abandoned in the eight deleted `docs/agents/` documents or in `model-notes.md` when I checked them myself. I have one SHOULD FIX: one line of the report's rule-accounting table (why "start in fresh context" was safe to drop) cites the wrong part of the framework as its replacement. It doesn't reflect an actual gap in the project's rules — `docs/state.md` already carries the real protection, untouched by this round — but the stated reason is wrong, and Brain re-checking that specific line is a cheap, worthwhile fix before or shortly after merge. Zero blockers. I'd call this ready to merge once that one line is corrected or Brain judges it not worth blocking on.
