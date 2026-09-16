# Active brief

Status: **queued, not started**.

Identifier: **`014-2026-09-16-per-artwork-printing-dates`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

> **Amended 2026-09-16, before issue:** the project adopted the shared agent
> framework. The executor seat is now the **Builder**, with a standing
> **Verifier**; the reading list, checkout, branch, push and report sections
> below were updated to match. Part B step 3 gained one neutral lead. The task
> itself is otherwise unchanged from the brief as queued on 2026-09-01.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on completion move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (zero-padded, check the archive
for the last-used number — 013 is the latest; this brief is 014) and replace it with the next
one, or leave a one-line "no brief queued" placeholder. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — topology, the non-negotiable project
   invariants, and the evidence table for what you touch. They outrank
   convenience.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract): modes, ground rules, and the
   completion-report shape.

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

   One lead, unverified: an unreviewed, never-accepted run of round 13
   (git ref `preserve/round13-alt-run-1bec139`) cited a different Konami
   page for the same boundary — the `yugioh-card.com/en/limited/` index page
   as captured by the Wayback Machine on 2010-10-05. Nothing it says about
   that page has been checked. If you use it, re-fetch the capture yourself,
   quote what it actually says, and state what a capture five weeks after
   the date can and cannot establish. Do not copy text from that ref.
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

## Expected suite state

The full suite is green as of the SHA you are branching from: **1029
tests, OK, 25 skipped**, and the process exits. The 25 skips are the engine
tests that need `ocgcore` and pinned checkouts. (1013 before the framework
adoption; it added the delivery-check and role-neutrality tests.)

If you see errors, they are yours to explain — do not wave them through as
"pre-existing Windows problems". That phrase covered a real defect until
recently: a held-open report file failed the write *and* left a non-daemon
thread spinning so the suite process never exited. Both are fixed. A hang
after the results print is a bug, not slowness.

## Git expectations

Work only in the Builder checkout, `.worktrees/builder/`. Fetch
`origin/main` and create branch `builder/per-artwork-printing-dates` from
it. Commit there in focused commits, then push that branch to `origin`. Do
not push `main`, and do not merge.

Before ending the round, write your completion report from inside
`.worktrees/builder/` with
`python3 tools/report.py write --task 014-2026-09-16-per-artwork-printing-dates`
(use `python` if that is what resolves), in addition to displaying it. Write
it after your final commit, so its recorded head matches the pushed branch:
the Verifier's delivery check compares the two.

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

---

## Outcome — accepted 2026-09-16, merged

Delivered by the Builder at `4c550ab4b82e38f575377ede6eed249c989eeb6e` on
`builder/per-artwork-printing-dates`, base
`58c30b72725dfd0b08de9cc6f88d5108815e7fd5`. The first round run with a standing
Verifier; its delivery check passed and it reviewed that exact head. CI green at
that SHA. Brain merged it into `main`.

- **Part A.** One real in-scope gap: Polymerization's second-artwork identity
  (27847700) had its Duelist Pack: Yugi printing mapped to the base passcode.
  Corrected in release data, so both release-cutoff pools gain one card through
  derivation, not a forced include. Brain re-derived the page split on Yugipedia
  and the set date. Dark Magician's Arkana artwork is correctly absent (first
  TCG print 2015).
- **Part B.** The September 2010 date is stated by the PDF's page-1 body
  header, not its `/Title`. Attribution corrected. The April 2005 heading is
  literal; no change needed.
- **Verifier findings upheld (SHOULD FIX):** the enumeration was taken from
  `data/cards/index.json`, which only holds passcodes this repository already
  references. Querying the pinned `cards.cdb` directly gives 16 real far-alias
  rows with a base in Edison or Tengu, not 9, and the report also left two
  Neo-Spacian pairs unclassified. Reproduced by Brain. None of the unseen rows
  is a pure alternate artwork, and no shipped pool is shown wrong, but the
  roadmap's claim that every far alias was enumerated overstated the audit.
  Annotated on the roadmap; the corrected record is a later brief.
- **Verifier claim not reproduced:** it reported the `materialize` refusal as
  exiting 0. It exits 1. The defect underneath is real and is round 15.
- **Accepted substitution:** the Builder called the pool materialiser directly
  instead of the `materialize` command, because of that defect; `validate`
  shows no drift afterwards.
- **Found in adjudication, not by either role:** the tool-session Stop hook
  overwrites a role's canonical self-report, and the Verifier's delivery check
  reads only that file. This round's delivery passed by timing, not by design.
  Round 15.
- The unreviewed `preserve/round13-alt-run-1bec139` lead was not used.
