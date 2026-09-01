# Active brief

Status: **queued, not started**.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number) and replace it with the next one, or leave a
one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — coordination rules and the
   non-negotiable epistemic rules. They outrank convenience.
2. [`docs/agents/role-contracts.md`](../agents/role-contracts.md) — the
   Worker contract: your mode's rules, the ground rules, and the
   completion-report schema you must report back in. Note the report is
   now a MUST written from inside the round, not only displayed.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: SOURCE VERIFICATION

## Goal

Roadmap item 3 — **verify the March 2010 TCG banlist against period
primary sources and upgrade it honestly** — and, in the same round because
it is the same ground, land three already-researched April 2005 findings
that were produced by a round which never landed.

Two framework rounds in a row have gone by. This is project work again.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Part A — March 2010 to `verified`

`data/banlists/tcg/2010-03.json` is `completeness: complete`, transcribed
from Yugipedia and cross-checked against Format Library. Its source
`konami-limited-2010-03` is an Internet Archive capture of Konami's own
`yugioh-card.com/en/limited/` page, and its `reliability_notes` say
outright: *"Direct entry-by-entry verification against this archive
snapshot is still TODO."* Roadmap item 3 records that the Archive was
unreachable in the session that wrote it.

It is reachable now. Do the verification that note defers:

- Fetch the archived Konami page and check it **entry by entry** against
  all 132 canonical entries — name and status, both directions.
- Decide `complete` vs `verified` on the schema's own bar in
  `schemas/common.schema.json`: `verified` needs load-bearing claims
  corroborated by strong primary/period evidence, not modern community
  consensus. If the archived page covers only part of the list (say,
  Forbidden but not Semi-Limited), then only that part is primary-sourced —
  say so and pick the status the *weakest* load-bearing claim supports.
- `effective_date` and `superseded_by_date` need the same treatment as the
  contents. Do not let a page's capture date stand in for the date a list
  took effect.
- If it does reach `verified`, propagate to
  `formats/2010-03-edison/format.json`'s `implementation_status.banlist`,
  and re-check whether `overall` should move (it is a judgement
  conventionally bottlenecked by the weakest axis, with no derivation
  rule — see `docs/state.md`).

## Part B — land the stranded April 2005 findings

A Worker round run against a stale checkout duplicated roadmap item 2 and
never landed. Its transcription was superseded by `191630e`, but three
findings in it are additive and are recorded in `docs/state.md`. They also
sit on the local branch/tag `preserve/april-2005-40cc995` — read that
commit directly rather than working from the summary.

1. **A primary source for `superseded_by_date`.** `191630e`'s own notes
   name this as unclosed: the October boundary is sourced only via
   Yugipedia's dating convention. That branch has an official UDE page
   dated "EFFECTIVE OCTOBER 1ST 2005", Wayback capture `20051026142552` of
   `upperdeckentertainment.com/yugioh/uk/forbidden_advanced_new.htm`.
   Verify it yourself, then cite it on `data/banlists/tcg/2005-04.json`.
2. **Format Library's "previous status" markers are unreliable as a
   class** — 5 wrong for April 2005, 3 already recorded for March 2010,
   same failure mode (newly-printed cards defaulted to
   `previous: unlimited` where Yugipedia has "not yet released"). Current
   list membership matched exactly both times. Record the *class* on the
   source records, not one more incident note — and apply the lesson while
   doing Part A rather than rediscovering it.
3. **UDE Appendix A is the August 1, 2005 revision.** It proves the April
   list was still in force in August, not that it went unamended from
   April; with a pre-effective-date Pojo capture it brackets the period,
   alone it does not. Check whether the current `2005-04.json` wording
   already makes that distinction and correct it if not.

Part B must not change the April 2005 entry set or downgrade its
`verified` status — both were independently re-derived and stand. It adds
sourcing and corrects wording.

## Guard rails

- GOAT's generated list must stay entry-for-entry identical to the Ignis
  reference: content hash `0x28E9FC02`, asserted in five test files. If it
  moves, stop and report rather than re-pinning.
- Adding out-of-pool restricted entries is structurally safe —
  `_build_whitelist()` walks the pool — but each new
  `format.restricted-card-outside-pool` warning is a finding to confirm,
  not noise to absorb. The current warning count is 569.
- No new research document. Findings belong on the banlist records, the
  format notes, and the roadmap items.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`). Fetch
`origin/main`, branch from it (e.g. `worker/march-2010-verification`). Do
not merge to `main` yourself. Do not push. The guard will stop you if you
start in the primary checkout.

Before ending the round, write your completion report with
`python3 tools/report.py write --task <this brief's filename>` in addition
to displaying it — see `docs/agents/report-handoff.md`.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: what the archived Konami page actually covers, the entry-by-entry
  result in both directions, the status you chose and the specific evidence
  that supports it — and, if `verified` was not reached, exactly what is
  missing.
- Part B: each of the three findings, verified independently rather than
  taken from `state.md`, and where each landed.
- Confirmation the GOAT parity hash is unchanged, the April 2005 entry set
  is unchanged, and the warning-count delta with every new warning
  accounted for.
- Exact output of `validate`, `build --check`, the atlas check, and the
  full suite.
- Anything left genuinely uncertain, stated as uncertain.
