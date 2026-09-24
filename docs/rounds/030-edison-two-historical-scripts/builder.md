## Verified

All project commands ran with `/opt/homebrew/bin/python3.13` (`python3` here is 3.9), on macOS arm64, at commit `de08abf` (pushed; report commit sits on top and touches only docs).

- Seat start — `python3 tools/fw.py start --role builder --round 030-edison-two-historical-scripts` → exit 0 (`branch builder/030-edison-two-historical-scripts at 6c4f5a294d92`).
- Validator — `python -m retroformats validate` → exit 0, `0 errors, 569 warnings`. `main` (checked out in a scratch worktree) gives `0 errors, 569 warnings`. Sorted warning-line diff against `main`, complete:
  - gone: `format.erratum-known-divergence` for Edison, **Metalzoa**
  - gone: `format.erratum-known-divergence` for Edison, **Super Vehicroid - Stealth Union**
  - new: `format.parity-omits-historical` for GOAT, **Metalzoa**
  - new: `format.parity-omits-historical` for GOAT, **Super Vehicroid - Stealth Union**
  Nothing else differs. The 2-for-2 swap is the one the brief expected, for the reasons 029's reports give (the GOAT warnings were silent only while the state was a known gap).
- Build — `python -m retroformats materialize` (no `data/pools/` change; Edison 3674, Tengu 4563, unchanged) then `python -m retroformats build --check` (run after committing) → exit 0, tree clean afterwards.
- Full suite — `python -m unittest discover -t . -s tests -v` → exit 0, `Ran 1052 tests … OK (skipped=40)`. (029 head: 1057 / skipped 45. The five fewer tests and five fewer skips are the five removed Night Assailant engine tests; the skips are the engine tests, which run only with ocgcore.)
- Engine, locally — `python scripts/engine_env.py prepare --dest <scratch>/engine` → exit 0 (ocgcore built from the pinned source, Darwin arm64); `python scripts/engine_env.py run --dest <scratch>/engine --expect-at-least 40` → exit 0:
  `engine-tests: executed=40 skipped=0 failures=0 errors=0 (required: at least 40 executed, 0 skipped)`
- Engine, CI at my final code head `de08abf67a193a5d84a86a37b6c85b0a8ddb2c5b` — run https://github.com/cntrl-alt-lenny/edopro-retro-formats/actions/runs/35966114727: `check (3.10)`, `check (3.13)` and `engine` all success (`Ran 1052 tests` on both; engine job: `engine-tests: executed=40 skipped=0 failures=0 errors=0 (required: at least 40 executed, 0 skipped)`). The report commit after it changes docs only.
- Removed engine tests (all five are Night Assailant tests; the whole `NightAssailantEdisonTest` class, 45 → 40):
  `test_modern_night_assailant_cannot_return_itself`,
  `test_project_ignis_pre_errata_night_assailant_cannot_return_itself`,
  `test_historical_night_assailant_returns_itself_from_the_graveyard`,
  `test_with_another_flip_monster_present_the_era_card_may_choose_either`,
  `test_flip_effect_destroys_a_monster_the_opponent_controls_like_the_modern_card`.
  The identity test (`test_generated_rows_alias_the_modern_card_in_a_duel`) stays, now over two pairs. Metalzoa and Stealth Union test classes are unchanged from 029, so 029's scratch red runs still apply: `35898264802` (head `b78af8c`, "generated metalzoa script behaves like the modern card") and `35898274208` (head `ff1f56a`, "generated stealth script behaves like the modern card"): both `engine` jobs failed, `check` jobs green (read with `gh run view`). I did not re-run new red runs, and I did not mutate with Ignis's scripts, because the brief forbids opening them.
- Night Assailant and lists — `git diff main HEAD -- data/errata/night-assailant.json` → empty. `git diff main HEAD --stat -- dist/lflists/` → only `2010-03-edison.lflist.conf` (2 deletions, 2 additions): `-3897065 3 --Super Vehicroid - Stealth Union`, `-50705071 3 --Metalzoa`, `+600000001 3 --Metalzoa (pre-errata)`, `+600000002 3 --Super Vehicroid - Stealth Union (pre-errata)`. Edison still names `16226786` with count 1 (as on `main`; the `+16226786` line I saw mid-work was the diff against 029's head). GOAT and Tengu lists are byte-identical to `main`; `GOAT_HASH 0x28E9FC02` is asserted by `tests/test_custom_cards.py` and the suite is green.
- `grep -rn 600000003 data/ dist/ retroformats/ tests/` → no output, exit 1. Matches under `docs/`: only `docs/rounds/029-…/builder.md`, `docs/rounds/029-…/verifier.md` and `docs/rounds/030-…/brief.md`, the historical round reports and this round's brief; they describe what was delivered and rejected, and stay as history.
- Materializer test tightened — `tests/test_migration_materializer.py`. The old per-field "must differ" exemption is replaced by `expected_after_round_029()`: for `erratum-metalzoa` and `erratum-super-vehicroid-stealth-union` only, the frozen materialized target with `coverage` and the single `implementation_metadata` entry replaced by pinned content (exact `custom-script` coverage; `status: partial`, `tested: true`, the `reason` string assembled from the frozen record's own `gap_reason`/`gap_sources`); on-disk must equal that dict and its bytes. Every other record is compared with its target exactly, as on `main`. Passes at head (`Ran 17 tests … OK`). Deliberate stray edits (each applied to the on-disk record, test run, file restored; `git status` clean after) all fail `test_every_target_matches_the_real_on_disk_file_exactly` with `AssertionError: Lists differ: [] != ['<record id>']` from `materialized content differs from the on-disk file`:
  - metalzoa `coverage.script` → `…c600000009.lua`
  - metalzoa `implementation_metadata[0].status` → `complete`
  - metalzoa `implementation_metadata[0].reason` + `" x"`
  - stealth-union `coverage.historical_passcode` → `600000001`
  - stealth-union `implementation_metadata[0].tested` → `false`
  - stealth-union `review.status` → `draft` (a field outside the two, to show the whole record is pinned)
- `python scripts/generate_format_atlas.py --check` → exit 0; `python3 tools/fw.py check` → `0 error(s), 0 warning(s)`.

## Not verified

- A real EDOPro client loading `dist/databases/retro-formats.cdb` and `dist/scripts/` (as in 029; only the headless engine ran).
- No new red CI runs at this head; the two 029 red runs are cited as the brief allows. I did not re-mutate the scripts locally.
- The `custom-card.authorship-not-original` rule, the two remaining scripts' `authorship` fields and the "Scripts are original" wording in `docs/errata.md` / `dist/README.md` are as 029 delivered them. I did not re-measure similarity (that would mean reading Ignis's scripts, which the brief forbids) and did not relabel; the brief's 0.27 / 0.31 measurements are Brain's.
- Windows; Python 3.10 locally (`check (3.10)` in CI passed at the exact head).

## Changed

- `data/errata/night-assailant.json` — restored to `main` (drops 029's never-merged `custom-script` coverage and `reference_identities` entry).
- `data/custom-cards/c600000003.{json,lua}`, `dist/scripts/c600000003.lua`, the `600000003` row in `data/cards/index.json` and in `dist/databases/retro-formats.cdb` — removed; `dist/lflists/2010-03-edison.lflist.conf` regenerated (Night Assailant back to `16226786 1`).
- `tests/engine/test_edison_historical_scripts.py` — Night Assailant class, its constants and its helper removed; identity test over two pairs; docstring says two cards.
- `tests/test_custom_cards.py`, `tests/test_shadow_migration.py`, `tests/test_tengu_format.py`, `tests/test_yugi_kaiba_format_gate.py` — 029's re-pinned counts moved from three cards to two: two swaps, new Edison hash `0xD5E90AFA` (and the pre-029 hash `0x8432B710` is still reproduced by swapping the two codes back), known-gap 40 / custom-script 2. These assertions rebuild the old values from the new ones, so nothing is loosened.
- `tests/test_migration_materializer.py` — tightened as above.
- `.github/workflows/ci.yml`, `docs/engine-testing.md` — engine floor 45 → 40 (exactly the five removed Night Assailant tests); engine doc table and card count say two cards.
- `dist/README.md`, `docs/errata.md` — say two generated cards; hazards paragraph no longer cites Night Assailant as having the reference identity.
- `docs/roadmap.md` item 7 — Night Assailant held back pending a licence-clean script and better evidence for its optionality and targeting, pointing to round 029's Verifier report; remaining count fixed (43 besides Night Assailant); the general GOAT-parity hazard kept, without naming a card that has the identity.
- `docs/state.md` — not changed.
- One code commit (`de08abf`) rather than several: the removal, the regenerated `dist/` and the re-pinned tests must land together for `build --check` and the suite to be green at any commit.

## Open questions

- None that block. The same thin-evidence question 029 raised for Night Assailant (optional vs mandatory, targeting) is now parked in the roadmap, not in the canonical record, as the brief asked.
- Stealth Union's similarity to Ignis's script (0.31) stays as the brief measured it; this round does not revisit it.
