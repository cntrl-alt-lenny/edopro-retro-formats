<!-- fw-report
round: 032-derived-scripts-licence
role: verifier
branch: verifier/032-derived-scripts-licence
head: bcf1419916b46524f73c0d7060bf7318490ded93
os: macOS 27.0
python: 3.13.15
written: 2026-09-27T17:47:18Z
-->
Reviewed commit: `bcf1419916b46524f73c0d7060bf7318490ded93` (`origin/builder/032-derived-scripts-licence`, as pinned by `fw.py start`), against `origin/main` `b50dc49` and round 031's head `3a3b409`. Code head: `2e5abb5`; the two later commits are the Builder's report only.

Commands I ran myself, from my own checkout (`.worktrees/verifier`, branch `verifier/032-derived-scripts-licence`). `python3` here is 3.9.6, so every project command used `/opt/homebrew/bin/python3.13` (3.13.15):

- `python3 tools/fw.py start --role verifier --round 032-derived-scripts-licence` — exit 0.
- `git diff --quiet 3a3b409 HEAD -- dist/lflists/ dist/databases/` — exit 0: Edison, Tengu and GOAT lists and `retro-formats.cdb` byte-identical to round 031's head.
- `python -m unittest discover -t . -s tests` — exit 0, `Ran 1081 tests … OK (skipped=59)`; the 59 skips are the engine tests.
- `python -m retroformats validate` — exit 0, `0 errors, 563 warnings`; the same at `3a3b409` (scratch worktree), and the sorted warning lines are identical (`diff` exit 0).
- `python -m retroformats build --check` — exit 0. `python3 tools/fw.py check` — `0 error(s), 0 warning(s)`.
- `python scripts/engine_env.py prepare --dest <scratch>/engine` — exit 0 (ocgcore from the pinned source, macOS arm64); `run … --expect-at-least 59` — exit 0, `engine-tests: executed=59 skipped=0 failures=0 errors=0`. `tests/engine/test_shared_historical_scripts.py` and `test_edison_historical_scripts.py` are unchanged since `3a3b409`; the floor rose 56 → 59, the three tests in `tests/engine/test_script_origin.py`.
- **Upstream diffs:** fetched `official/c{67959180,41006930,46668237,16067089,37383714}.lua` and `COPYING` from CardScripts `383bfbd6…` and ran `diff` against each derived script (results under Findings).
- **Modern-script mutations** (each reverted with `git checkout -- dist`, tree clean): replacing each derived script in `dist/scripts/` with Ignis's modern script fails exactly its card's difference tests under both `edison` and `tengu` (Goddess 2 failures, Strike Ninja 2, Green Baboon 4, Rise 2, Soul Rope 2). So the rebase kept every test able to fail.
- **Validator mutations** (each reverted): record `modified.summary` changed so the header is stale → `custom-card.authorship-header-mismatch`; `upstream.revision` not the pin → `custom-card.bad-authorship`; `modified` deleted → 3× `bad-authorship`; derived record claiming `MIT` → `bad-authorship`; derived record relabelled `original`/`MIT` with the AGPL header left in place → 2× `authorship-header-mismatch`; an `--Upstream:` line added to an original script → `authorship-header-mismatch`; the SPDX line removed from a derived script → `authorship-header-mismatch`; `kind: "adapted"` → `bad-authorship`. Each gave `1+ errors`, and every one reverted to 0.
- **Gate failure:** put round 031's Goddess of Whim script back (`git show 3a3b409:…c600000004.lua`) with an `MIT` SPDX line and an `original`/`MIT` record, so validate stays at 0 errors; `engine_env.py run` then fails `test_every_original_script_measurably_differs_from_ignis_script_for_its_alias` with "labelled original but its line-sequence ratio against official/c67959180.lua is 0.72 (limit 0.4 …)", `executed=59 skipped=0 failures=1`. Reverted.
- **Gate calibration:** ran `retroformats.script_similarity.measure` / `too_close` myself on all eight current scripts and on every known close case (table below).
- `cmp` of Ignis's `COPYING` at the pin with `LICENSES/AGPL-3.0-or-later.txt` and `dist/scripts/LICENSE-AGPL-3.0-or-later.txt` — both identical; `dist/scripts/LICENSE-MIT.txt` equals the root `LICENSE`. Read `dist/scripts/LICENSES.md`, the `README.md` diff and each derived header.
- Malefic (item 6): fetched from Yugipedia's API `Card_Errata:Malefic_Blue-Eyes_White_Dragon`, `Duelist_Pack:_Kaiba`, `Set_Card_Galleries:Duelist_Pack:_Kaiba_(TCG-EN-UE)`, `Silver_Dragon_Value_Box` and `Duelist_Pack:_Yugi_&_Kaiba_Special_Edition` before reading the Builder's finding.
- `gh api …/commits/bcf1419…/check-runs` — `check (3.10)`, `check (3.13)`, `engine` success; run `36334390276` engine log: `engine-tests: executed=59 skipped=0 failures=0 errors=0`.

| script vs Ignis's script for its alias (Builder's `measure`, limit 0.40) | ratio | shared 4-line windows | gate |
|---|---|---|---|
| Metalzoa `c600000001` (original) | 0.265 | 0/44 | pass |
| Stealth Union `c600000002` (original) | 0.314 | 1/84 | pass |
| Malefic BEWD `c600000008` (original) | 0.126 | 0/65 | pass |
| Goddess `c600000004` (derived, head) | 0.952 | 21/28 | not measured by the gate (derived) |
| Strike Ninja `c600000005` (derived, head) | 0.955 | 33/41 | — |
| Green Baboon `c600000006` (derived, head) | 0.921 | 17/29 | — |
| Rise `c600000007` (derived, head) | 0.987 | 31/35 | — |
| Soul Rope `c600000009` (derived, head) | 0.958 | 25/33 | — |
| Night Assailant `8f1deb6` | 0.692 | 11/46 | flag |
| Goddess `3a3b409` | 0.719 | 4/29 | flag |
| Strike Ninja `3a3b409` | 0.506 | 1/36 | flag |
| Green Baboon `3a3b409` | 0.609 | 2/35 | flag |
| Rise `3a3b409` | 0.579 | 3/36 | flag |
| Soul Rope `3a3b409` | 0.711 | 8/38 | flag |

## Findings

- [NOTE] **Derived diffs are only the period change plus the header.** Against the pinned upstream files: Goddess drops `e1:SetCountLimit(1)`; Strike Ninja changes `SetCountLimit(1,id)` to `SetCountLimit(1)`; Green Baboon adds `EFFECT_FLAG_DAMAGE_STEP` and drops `c:IsPreviousPosition(POS_FACEUP)`; Rise adds `EFFECT_FLAG_DAMAGE_STEP` only; Soul Rope adds `EFFECT_FLAG_DAMAGE_STEP` and drops `c:IsReason(REASON_EFFECT)`. The one other edit, in Goddess, Strike Ninja and Baboon, is `aux.Stringid(id,0)` → `aux.Stringid(<modern code>,0)`, needed because the generated row carries no strings; each header's modification line says so. Every `dist/scripts/` copy is byte-identical to its canonical script. Rebasing onto upstream changes some untested edges compared with round 031's scripts: Goddess halves with `/2` instead of rounding up, Baboon has no `EFFECT_FLAG_DELAY` and can miss timing, and Strike Ninja's cost filter now follows upstream's `aux.SpElimFilter`. Each is stated in the card's `not_reproduced` and raised in the Builder's Open questions, and none is a historical claim.
- [NOTE] **Licence notices meet what the AGPL asks and are visible from `dist/` alone.** Each derived header carries the SPDX line, the upstream URL at the pinned revision, Project Ignis's copyright notice verbatim as its README states it ("Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file."), a dated "Modified by edopro-retro-formats on 2026-09-27: …" line (section 5(a)), and a statement that the file is under AGPL-3.0-or-later with where the licence text is (5(b)). Upstream's own name comments are kept below the header. `dist/scripts/` holds `LICENSE-AGPL-3.0-or-later.txt` (byte-identical to Ignis's `COPYING`), `LICENSE-MIT.txt` and a generated `LICENSES.md` listing every script's licence and origin and naming the source repository. The root `README.md` names the five AGPL files. So someone who downloads `dist/scripts/` alone gets the notice and the licence text. The three `original` scripts start with `--SPDX-License-Identifier: MIT`.
- [NOTE] **The similarity gate classifies every known case correctly.** With the Builder's measure at limit 0.40, all six flagged cases score 0.506–0.719 and the three accepted originals 0.126–0.314 (table). The gap is 0.31 to 0.51, and the threshold sits nearer the accepted side, which is the cautious choice. The gate runs in CI's `engine` job (59 executed, 0 skipped), and I watched it fail on round 031's Goddess relabelled original. A missing upstream file fails rather than passes.
- [NOTE] **The calibration itself is not pinned by any test.** Nothing committed asserts that the six historical close cases are flagged. The limit could be raised later (say to 0.75) with every test still green. The report and the module's comment carry the numbers; a regression test would have to hold the old scripts as fixtures, which are themselves AGPL-derived. Brain may want a small fixture test (under AGPL, alongside the derived scripts) or a note that `ORIGINAL_MAX_RATIO` changes only with a brief.
- [NOTE] **Two narrow gaps in the mechanism, neither exploited here.** (1) For `derived`, the validator checks that `upstream.path` is a `.lua` path at the pinned revision, and the engine test checks the file exists. Nothing checks that it is the script for the card's own alias, so a record could credit the wrong upstream file and pass. All five records currently point at their alias's `official/` file. (2) The gate measures an `original` script only against Ignis's script for its own alias, so a script adapted from a *different* Ignis card would not be caught. Both are worth one line in the roadmap; neither affects this round's files.
- [NOTE] **The Malefic finding is supported by the passages it cites; I reached the same conclusion before reading it.**
  - The errata table's corrected-text caption pairs "DPKB-EN023 / Duelist Pack: Kaiba / (Unlimited Edition) / Silver Dragon Value Box".
  - `Silver_Dragon_Value_Box`: "na_release_date = September 13, 2013", "This bundle reprinted Duelist Pack: Kaiba with Problem-Solving Card Text", with "4 Duelist Pack: Kaiba booster packs (Unlimited Edition)".
  - `Duelist_Pack:_Yugi_&_Kaiba_Special_Edition`: "na_release_date = October 25, 2013".
  - `Duelist_Pack:_Kaiba`: "The English set was reprinted with Problem-Solving Card Text …", and it lists a separate English Unlimited Edition gallery. That gallery page carries no date.

  Every dated English source for the corrected text is from 2013 or later. I found no evidence of an English Unlimited printing with it before 2011-09-17, and no proof that none existed. "Inconclusive, record unchanged" is the right reading, and `data/errata/malefic-blue-eyes-white-dragon.json` is unchanged since `3a3b409`. I did not check the collector-box dates or the `Banish` page the Builder also cites; neither is load-bearing.
- [NOTE] **The validator change is stricter, not looser.** `custom-card.authorship-not-original` is replaced by `custom-card.bad-authorship` and `custom-card.authorship-header-mismatch`, as the brief authorises. For `original`, the new rule adds a required `licence: MIT` and a matching SPDX first line, and rejects any upstream fields or an `--Upstream:` header line. For `derived`, it requires a derivable source, the upstream's licence, the pinned revision, a copyright notice, an ISO date and a summary, each repeated on a fixed header line. All eight of my mutations were caught.

## Not verified

- A real EDOPro client loading the scripts or the licence files; only the headless engine ran.
- Whether the headers satisfy the AGPL in a legal sense. I checked them against sections 4 and 5 as written; the reading is the owner's (or counsel's).
- An English DPKB Unlimited printing date from any source outside Yugipedia; the pages read are live, not pinned revisions.
- The Builder's tests in `tests/test_custom_cards.py` one by one. I relied on my own validator mutations and the green suite.
- Windows; Python 3.10 locally (relied on `check (3.10)` at the exact head).

## Verdict

I believe round 032 does what its brief asks, and I have no blockers. The five close scripts are now honest adaptations: each diff against its pinned Ignis source is the header, the period edit and a string-id pointer, nothing a reviewer has to guess at, and every engine test still passes and still fails on the modern script under both formats. The licence is visible from the repository root and from `dist/scripts/` alone, and the AGPL text is byte-identical to Ignis's `COPYING`. The new validator rule catches every record/header mismatch I tried, and the similarity gate flags all six historical close cases while passing the three originals; I watched it fail in the engine run. Lists, database and warnings are byte-identical to round 031's delivered state, and CI is green at the exact head. The Malefic research is sound and correctly left inconclusive. My notes are refinements, not blockers: no test pins the calibration numbers, `derived` is not tied to the card's own alias file, and the rebase changes a few untested edges, all disclosed. I am confident in this verdict for the engineering and the licence mechanics; the legal adequacy of the notices remains the owner's call.
