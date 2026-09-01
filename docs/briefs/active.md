# Active brief

Status: **queued, not started**.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number — 013 is the latest) and replace it with the next
one, or leave a one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — coordination rules and the
   non-negotiable epistemic rules. They outrank convenience.
2. [`docs/agents/role-contracts.md`](../agents/role-contracts.md) — the
   Worker contract: your mode's rules, the ground rules, and the
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: DATA/SCHEMA

## Goal

Roadmap item **4b — per-artwork printing dates**. Far-alias alternate arts
are currently absent from cutoff-derived pools unless force-included.
Establish which ones actually mattered in-period, and encode those with
sources. Part B corrects one attribution defect found reviewing round 13.

## Starting SHA

Verify with `git log -1` on `main` before starting and note the actual SHA
in your report. `main` is green; keep it that way.

---

## Part A — far-alias alternate arts (roadmap 4b)

Background you can rely on, already established:

- BabelCDB models an **artwork variant** as an alias whose passcode is
  within `ARTWORK_OFFSET` (±10) of the base code. `releases.py`'s
  `_canonicalise()` folds those into the base card, so their printings
  correctly contribute dates to the base card.
- A **far alias** — alias distance ≥ 10 — is deliberately *not* folded. It
  is treated as a distinct card. If no release printing maps to it, it
  simply never enters a cutoff pool.
- That is the right default. This item is about the cases where it silently
  drops something a period player could actually have used.

Do:

1. **Enumerate the class, don't sample it.** From the pinned BabelCDB
   revision (`data/sources.json`'s `ignis-babelcdb`), list every row that is
   a far alias of a card in each canonical pool. Report the count per format
   before filtering — the size of the class is itself a finding.
2. **Separate three different things** and keep them separate in the
   report: (a) far aliases that are pure alternate *artwork* of a pool card;
   (b) far aliases that are a different *region/scope* of it — that is the
   `region_substitutions` mechanism's territory, already handled, so say so
   and leave it alone; (c) far aliases that are functionally different
   cards (pre-errata variants). Only (a) is in scope here.
3. **For each in-scope case, establish the printing history from release
   data, not from the cdb.** The question is whether that artwork had a
   printing released on or before the pool's `cutoff_date`. A cdb row
   existing proves EDOPro can represent it; it proves nothing about 2010.
4. **Encode only what the evidence supports.** Where a period printing is
   established, add it through the normal release/printing records so the
   pool derives it — do not hand-add pool entries, and do not reach for
   `force_include` unless the pool machinery genuinely cannot express the
   case, in which case explain why in the record.
5. If the honest answer for a format is "none of these mattered in-period",
   that is a perfectly good result. Say it, with the enumeration behind it.
   Do not manufacture inclusions to make the round look productive.

The named example in the roadmap is **Arkana's Dark Magician**. Treat it as
one case to check, not as the answer.

## Part B — correct one effective-date attribution

Round 13 landed a claim slightly stronger than its source, in exactly the
category this project guards hardest.

`data/banlists/tcg/2010-03.json`'s note says the September 2010 successor
PDF's *title* states "Effective September 1, 2010". Brain re-fetched that
PDF (`web.archive.org/web/20100923013922id_/`
`http://www.yugioh-card.com/en/limited/pdf/`
`Limited%20%26%20Forbidden%20Cards_10-09.pdf`) and read its document
information dictionary directly. The `/Title` is:

```
Limited & Forbidden Cards / Advanced Format - Sept 1, 2010
```

It does not contain the word "Effective". `/CreationDate` is
`D:20100811180154` (2010-08-11), which sits before the stated date and is
consistent with a list published ahead of taking effect.

Do:

1. Reword the note so it states what the title actually says. The
   conclusion — `superseded_by_date = 2010-09-01` — is supported and should
   stand; only the attribution changes.
2. `docs/roadmap.md` item 3 repeats the same phrasing. Fix it too.
3. The PDF's body text uses subsetted font encodings, so Brain could not
   read it. **If** you can extract the body reliably and it does say
   "Effective September 1, 2010", then cite the body rather than the title
   and say which page/line. If you cannot extract it, say so plainly and
   cite the title only. Do not assume the body says it.
4. Check whether the *April* record carries the same shape of claim about
   the UDE October page. That page's heading was reported as "EFFECTIVE
   OCTOBER 1ST 2005" — verify that is the heading text and not a summary of
   it, and correct it if it is not.

## Guard rails

- GOAT's generated list must stay entry-for-entry identical to the Ignis
  reference: content hash `0x28E9FC02`. If it moves, stop and report rather
  than re-pinning.
- Current validator baseline is **0 errors, 569 warnings**. Any new warning
  is a finding to explain, not noise to absorb.
- Entry sets of the April 2005 and March 2010 banlists must not change.
  Part B is wording and sourcing only.
- `dist/` is generated — never hand-edit it; regenerate with
  `python -m retroformats build`.
- No new research document. Findings belong on the release/source records,
  the format notes, and the roadmap item.

## Known-failing tests — not yours to fix

On Windows, `tests/test_report.py`'s
`test_readers_during_concurrent_writes_never_see_torn_content` errors with
`PermissionError [WinError 32]`: `os.replace` loses to a concurrent reader
holding the destination open. It is a known, recorded, non-blocking defect
(see `docs/state.md`) and CI is unaffected. Report it if you see it; do not
fix it in this round, and do not let it stop you calling the suite clean.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`). Fetch
`origin/main`, branch from it (e.g. `worker/per-artwork-printing-dates`).
Do not merge to `main` yourself. Do not push. The guard will stop you if
you start in the primary checkout.

Before ending the round, write your completion report with
`python3 tools/report.py write --task <this brief's filename>` (use
`python` if that is what resolves) in addition to displaying it — see
`docs/agents/report-handoff.md`.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the enumerated far-alias class per format with counts, the (a)/(b)/(c)
  split, what you established about each in-scope case's period printing and
  from which source, and what you encoded versus deliberately left out.
- Part B: the exact corrected wording, whether you could read the PDF body,
  and the result of the April cross-check.
- Confirmation the GOAT parity hash is unchanged, both banlist entry sets are
  unchanged, and the warning-count delta with every new warning accounted for.
- Exact output of `validate`, `build --check`, and the full suite.
- Anything left genuinely uncertain, stated as uncertain.
