# 030-edison-two-historical-scripts: Edison historical scripts, without Night Assailant

Tier: 2
Mode: implementation
Supersedes: 029-edison-historical-scripts, rejected at
`8f1deb65200af976a7d2bc03e6a2069533425f78`. That round delivered the
generated-card path and three cards. Night Assailant's script
(`c600000003.lua`) matches Project Ignis's AGPL-3.0-or-later
`official/c16226786.lua` in structure, function names and most of its lines.
Normalised, the line-sequence similarity ratio is 0.69; Brain re-measured
this at the pinned CardScripts revision `383bfbd6`. Yet the code, the
records, the docs and a validator rule all call the script original, and
whether it is original is unclear. Night Assailant's period behaviour also
rests partly on assumptions its record does not support. **The owner decided
on 2026-09-23 to hold Night Assailant back.** This round ships the other two
cards, which measured 0.27 (Metalzoa) and 0.31 (Stealth Union) and differ
from upstream in structure and mechanism, and fixes one test that round 029
loosened more than needed.

## Goal

Round 029's work lands, but with only Metalzoa (`600000001`) and Super
Vehicroid - Stealth Union (`600000002`). Night Assailant stays exactly as it
is on `main`: a known gap, with the modern card in Edison's list. Nothing in
the repository claims otherwise.

## Context

- This branch starts from round 029's delivered work, so everything 029 built
  is already here. Read `docs/rounds/029-edison-historical-scripts/brief.md`,
  `builder.md` and `verifier.md`. The Verifier's findings are the reason for
  this round.
- The same project documents as round 029: `AGENTS.md` (evidence table rows
  for canonical data, `retroformats/` code and engine tests),
  `docs/agents/FRAMEWORK.md`, `docs/agents/roles/worker.md`.
- Do **not** open or read Project Ignis's scripts for any card. That includes
  Night Assailant's, and any card you consider for later work.

## Scope and non-goals

In scope:

1. **Remove Night Assailant from the generated-card path.** When you are done:
   - `data/errata/night-assailant.json` is byte-identical to `main`, which
     drops the `reference_identities` entry round 029 added.
   - `data/custom-cards/c600000003.*` and `dist/scripts/c600000003.lua` no
     longer exist, and the generated database has no `600000003` row.
   - `data/cards/index.json` has no `600000003` row.
   - Edison's list names `16226786` with count 1, as on `main`.
   - The engine tests, generator tests and docs that mention Night Assailant
     as implemented (`dist/README.md`, `docs/errata.md`,
     `docs/engine-testing.md`, `docs/roadmap.md` item 7) say what is now
     true.
   - Don't assign `600000003` to another card in this round.
2. **Record why it was held back.** Put a short note in `docs/roadmap.md`
   item 7 (not in the canonical record) saying Night Assailant is held back
   pending a licence-clean script and better evidence for its optionality and
   targeting, with a pointer to round 029's Verifier report. Keep the general
   hazard 029 documented about GOAT parity walking a record's states when a
   `known-gap` becomes `custom-script`. It stays true for future cards, but it
   should no longer cite Night Assailant as a card that has the reference
   identity.
3. **Tighten `tests/test_migration_materializer.py`.** Round 029's exemption
   lets the listed fields of the edited records hold any content, as long as
   it differs from the frozen target. Replace it so the test pins exactly
   what those fields must now contain, for the two remaining records only. A
   stray edit to either record's `coverage` or `implementation_metadata` must
   fail the test. Show that it does.
4. Keep the generator, validator rules, harness and the two remaining cards
   as round 029 delivered them, apart from what items 1–3 require. If you
   find a defect in them, report it; fix it only if the fix is small and
   inside this scope.

Non-goals:

- No new card, including the five intermediate-state and 38 Tengu-coupled
  candidates 029 listed. No chronology or evidence change to any record.
- No change to GOAT or Tengu output. The GOAT hash `0x28E9FC02` must not
  move.
- No change to what the CI `check` job runs. The engine job's required count
  falls by exactly the number of Night Assailant engine tests removed. That
  is expected and is not a weakening, provided every removed test is a Night
  Assailant test; list them.
- Don't rewrite the two remaining scripts. Don't relabel their authorship
  unless you find they are not what they claim; if so, stop and report.

## Invariants

- History and representability stay separate (`AGENTS.md`).
- Evidence in a record is added to, never replaced (`AGENTS.md`). Restoring
  `night-assailant.json` to `main` is the exception: this round explicitly
  removes 029's never-merged edit to it.
- No regression test is loosened (`AGENTS.md`). After item 3, every record
  except the two named ones is checked exactly as on `main`. The two named
  ones are checked against pinned exact content, not just "different".
- Validator: 0 errors. Expected: 569 warnings, the same as `main`. Two Edison
  `format.erratum-known-divergence` warnings go (Metalzoa, Stealth Union), and
  two GOAT `format.parity-omits-historical` warnings come (the same two
  cards), for the reasons round 029's reports give. Explain any other
  difference line by line against `main`.

## Acceptance criteria

- Against `main`, the net diff contains round 029's path with exactly two
  generated cards. Every Night Assailant file, row, list line and record
  matches `main`.
- `build --check` is clean, GOAT and Tengu lists are byte-identical to
  `main`, and the GOAT hash is unchanged.
- Both remaining cards' engine tests pass in CI's `engine` job at your final
  head, with 0 skipped. Each still fails on the modern behaviour: cite round
  029's red runs `35898264802` and `35898274208`, or new ones if the tests
  changed.
- The materializer test fails on a stray edit to either remaining record, and
  passes at head.

## Required evidence

- `python -m retroformats validate`, with counts and a sorted diff of the
  warning lines against `main`.
- `python -m retroformats build --check`
- `python -m unittest discover -t . -s tests -v`, with the count and skips.
- `python scripts/engine_env.py prepare` then `run --expect-at-least N` on
  macOS or Linux, and the CI run URL at your final head with the engine job's
  `executed=… skipped=…` line.
- `git diff main HEAD -- data/errata/night-assailant.json dist/lflists/`,
  showing only the two expected Edison lines.
- `grep -rn 600000003` over `data/ dist/ retroformats/ tests/`, showing
  nothing. List any matches in `docs/` and say why each one stays.
- The failing run of the tightened materializer test on a deliberate stray
  edit.

Your report (`docs/rounds/030-edison-two-historical-scripts/builder.md`) has
the Worker card's sections.
