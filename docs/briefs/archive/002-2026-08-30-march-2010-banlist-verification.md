# Active brief

Status: **queued, not started**. One brief lives here at a time; when
Worker completes it (accepted or rejected by Brain), move this file to
`docs/briefs/archive/<date>-<slug>.md` and replace it with the next one, or
leave a one-line "no brief queued" placeholder.

---

## MODE: SOURCE VERIFICATION

## Goal

Determine whether `data/banlists/tcg/2010-03.json`'s `completeness` field
can be honestly upgraded from `"complete"` to `"verified"` by actually
reconciling its 46 entries, card by card, against the Konami primary
source already cited in `data/sources.json` — and if the reconciliation
holds, make the upgrade; if it doesn't, or the source turns out not to
support that, report exactly what you found instead of assuming either
outcome going in.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA in
your report.

## Why this is next

Roadmap item 3 (`docs/roadmap.md`, Phase 1) says: "Verify March 2010
against the Konami archive snapshot (Internet Archive was unreachable this
session); upgrade the banlist to `verified`." But `data/sources.json`
already has a `konami-limited-2010-03` entry — a Wayback Machine URL
pointing directly at Konami's own official list page, retrieved
2026-08-19 — and it's already cited in `data/banlists/tcg/2010-03.json`'s
`sources` array alongside the Yugipedia transcription. So either the
archive access failure the roadmap note describes was resolved later that
same session (the source's `retrieved` date matches) and the actual
card-by-card comparison was simply never done or never reflected in the
`completeness` field, or something else is blocking it that isn't written
down anywhere. This brief exists to find out which, directly, rather than
have Brain guess.

## Relevant context

Read:

- `data/banlists/tcg/2010-03.json` — the record in question.
- The `konami-limited-2010-03` and `yugipedia-march-2010` entries in
  `data/sources.json` (grep for both ids).
- `schemas/common.schema.json`'s `implementationStatus` definition — the
  exact bar for `verified` is "complete AND the load-bearing historical
  claims are corroborated by strong primary/period evidence, not merely
  modern community consensus." `complete` requires "cross-checked against
  at least one independent... source." The banlist is already `complete`;
  the question is whether it also clears the higher `verified` bar.
- `docs/errata.md` or `docs/releases.md` only if you need to understand
  how `completeness` upgrades are handled elsewhere in this codebase as a
  precedent for what "doing the work, not just changing the label" looks
  like (skim, don't deep-read).

You do not need to read `docs/roadmap.md` beyond item 3, or any Tokyo Dome
/ Edison rules / erratum material — unrelated to this task.

## Scope

1. Fetch the archived Konami page at the `konami-limited-2010-03` URL
   (`http://web.archive.org/web/20100825095431/http://www.yugioh-card.com/en/limited/10_03_list.html`).
   If it's unreachable from your environment, say so plainly and stop —
   do not substitute a different source for the primary-source role
   without flagging that substitution explicitly.
2. Extract the actual Forbidden / Limited / Semi-Limited card list from
   that page as it reads.
3. Compare it, entry by entry, against `data/banlists/tcg/2010-03.json`'s
   `entries` array (46 entries: card name + status). Note any card present
   in one list and not the other, or with a different status, by name.
4. If the two match exactly: update `completeness` to `"verified"` and
   extend `notes` to state plainly that a card-by-card reconciliation
   against the archived Konami page was performed and matched exactly
   (name the date you did this). Do not just change the enum value without
   this record of what was actually checked.
5. If they don't match, or the source can't be reached, or the page's
   list is genuinely ambiguous in some way (OCR artifacts, missing
   section, etc.): leave `completeness` as `"complete"`, do not touch the
   `entries` array, and report the discrepancy/blocker in full detail
   instead. A partial or uncertain reconciliation is not grounds for
   upgrading the status — see "Do not" below.

## Non-goals

- Do not change any `entries` array value (card, passcode, or status)
  based on this reconciliation without flagging it to Brain first as a
  separate finding — this brief is about verifying the *existing* data,
  not correcting it. If you find a genuine discrepancy, report it; don't
  silently "fix" the JSON to match your reading of the archive page.
- Do not touch `data/banlists/tcg/2005-04.json` (the GOAT banlist,
  roadmap item 2) — different, larger task, not this brief.
- Do not touch `formats/2010-03-edison/format.json`'s own
  `implementation_status.banlist` field unless you've confirmed it
  currently just mirrors the banlist's `completeness` (check first;
  update only if it's supposed to track it and doesn't automatically).
- Do not add a new source to `data/sources.json` unless the existing two
  entries turn out to be insufficient for some reason you document.

## Protected invariants

- `tests/test_repo_data.py::test_edison_banlist_counts` and other Edison
  tests must still pass — they check `entries`, not `completeness`, so
  they shouldn't be affected by a `completeness` change alone, but confirm
  this rather than assume it.
- `python -m retroformats validate` must still report the same error/
  warning count for this banlist (0 errors either way; check whether any
  warning specifically about `completeness` disappears, which would be
  expected and fine).
- Any Wayback Machine fetch you do is read-only evidence gathering — this
  brief doesn't touch `dist/`, and `build --check` should be a no-op
  either way.

## Required investigation

1. Confirm the Wayback URL is actually reachable from your environment
   before concluding anything either way about the source itself.
2. Do the full 46-entry reconciliation yourself — don't sample a few
   entries and extrapolate "looks right."
3. Check whether `formats/2010-03-edison/format.json`'s
   `implementation_status.banlist` field is meant to mirror
   `data/banlists/tcg/2010-03.json`'s own `completeness`, or is
   independently set — read `docs/format-schema.md` if the relationship
   isn't obvious from the two files alone.

## Acceptance criteria

- A clear, evidenced answer to "does this reconcile," not a guess.
- If upgraded: `completeness: "verified"`, `notes` records what was
  checked and against what, `entries` array unchanged.
- If not upgraded: `completeness` unchanged, and the report explains
  exactly why (unreachable source / mismatch found — name it / genuine
  ambiguity — describe it).
- Full test suite still passes either way.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Commit on a new branch (e.g. `worker/verify-2010-03-banlist`). Do not
merge to `main` yourself. Do not push unless asked.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Whether the archive page was reachable, and from where you tried it.
- The full reconciliation result: match, or the specific discrepancies
  found (name every card involved).
- What you changed, file by file, if anything.
- Exact output of the three validation commands.
- Anything left genuinely uncertain — state it as uncertain, don't round
  it to a clean yes/no if the evidence doesn't support one.
