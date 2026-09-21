# Active brief

Status: **queued, not started**.

Identifier: **`022-2026-09-21-segoc-period-evidence`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (021 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — invariants, especially evidence before
   confidence, evidence being added to rather than replaced, and historical
   truth versus engine representability.
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. For Part A: [`docs/research/edison-rules.md`](../research/edison-rules.md) —
   row 9 of the evidence table, the Decision section and the Adversarial review.
5. For Part 0: the archived brief
   [`021-2026-09-21-near-edison-faq-captures.md`](archive/021-2026-09-21-near-edison-faq-captures.md)
   and its Outcome.

Do not read the rest of `docs/research/`.

---

## Part 0 — MODE: DOCUMENTATION — one carried correction

Round 21's research text in `docs/research/edison-behaviour-gaps.md` says there
were no 2009-2010 Konami Card FAQ captures after the January 2009 rows, and the
`default_ik` source record in `data/sources.json` says the timemap found no
later capture. The timemaps also list HTTP-302 rows through April 2009, which
redirect to non-FAQ pages (see round 21's Outcome for the counts Brain
observed). Re-check them yourself, then make both texts say exactly what was
searched: how many rows of each status, what the redirects led to, and that no
later HTTP-200 FAQ-content capture exists in the window. Add to what is there;
do not remove the existing evidence. No conclusion changes.

## Part A — MODE: HISTORICAL RESEARCH

### The question

Edison's rule profile (`data/rule-profiles/tcg-mr1-edison.json`) omits two
engine flags, `DUEL_TCG_SEGOC_NONPUBLIC` and `DUEL_TCG_SEGOC_FIRSTTRIGGER`, and
records them as evidentially unresolved. `edison-rules.md` row 9 explains why:
the official Rulebook editions of 2008-2011 describe a simple two-tier ordering
of simultaneous triggers and never address the two specific mechanics those
flags implement — (a) triggers from a hidden or non-public zone being folded
into the main ordering pass, and (b) triggers from several different
simultaneous events being restricted to the earliest event. The only claim that
the stricter practice existed in 2010 is a 2012 forum post.

**Establish whether any official or officially sanctioned material in effect
in the TCG between about 2009 and the Edison snapshot (2010-04-24) addresses
either mechanic, and what it says.** Candidate families, not an exhaustive
list: Konami judge-program materials and judge guides; Konami tournament
policy and its annexes; official rulings articles or rules columns on Konami's
site; per-set rulings documents; officially published event FAQs. Frame it
neutrally: a source showing the simple ordering applied, one showing a
stricter ordering applied, and "nothing addresses it" are all useful.

### Required investigation

1. For each source family you search: what you searched, how, what exists in
   the period window, and what each item does and does not establish. A
   failed search is evidence about the search, not proof of absence.
2. For anything you find: its own date, the date it describes, whether it is
   contemporary or retrospective, and whether it is official, officially
   sanctioned, or community material. Keep those apart.
3. Keep the two mechanics separate. A source about one does not settle the
   other, and a source about SEGOC in general does not settle either unless it
   actually describes that mechanic.
4. Keep historical truth and engine representability separate. What the
   period rule was is one question; whether a flag reproduces it exactly is
   another, and `edison-rules.md` shows these flags implement narrower
   behaviour than their names suggest.

### Scope

- `docs/research/edison-rules.md` — findings, added to row 9's record without
  removing what it already says.
- `data/sources.json` — a record for every source you cite, stating what it
  does and does not establish.

### Non-goals

- **No change to the rule profile, to `formats/`, or to any engine flag.**
  If the evidence would support adding or confirming the omission of either
  flag, stop at the finding and set out the recommendation, with what an
  engine test would need to show. Changing the profile is a separate round.
- The other four unresolved flags, and the ignition-priority question.
- No canonical errata change, no `dist/`, validator, schema or test change.

### When to stop

If a source is plausibly relevant but its date or authority cannot be
established, record it as unresolved rather than weighing it. If the question
cannot be advanced from the families you can reach, record exactly what you
searched and stop; that is a complete result.

## Shared

### Base

Cut from `origin/main`. Record the literal starting SHA.

### Protected invariants

- Evidence before confidence; evidence added to, never replaced.
- Validator baseline 0 errors, 569 warnings; suite passing; GOAT hash
  `0x28E9FC02`; banlist entry sets unchanged.
- Gates green at your head, CI included. If a gate cannot pass within the
  brief, stop and report; never bypass a check.

### Acceptance criteria

- Part 0: both texts state the redirect rows accurately, with the existing
  evidence kept.
- Part A: a sourced answer for each mechanic separately, or a specific account
  of what was searched and why it does not settle it.
- Every cited source registered with what it does and does not establish.
- Every changed record's base and head versions side by side.
- No rule-profile, `formats/`, errata or `dist/` change.

### Required evidence

For every claim: URL or file, the passage read, and for archived pages the
served memento timestamp. `python -m retroformats validate`,
`python -m retroformats build --check` and
`python -m unittest discover -t . -s tests -v`, with real output and exit
status, on Python 3.10 or newer.

### Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/segoc-period-evidence` from `origin/main`. Focused
commits; push the branch; never push `main`; never merge; never bypass a local
check. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from
inside `.worktrees/builder/` with
`python3 tools/report.py write --task 022-2026-09-21-segoc-period-evidence`
(Python 3.10+), as well as displaying it.

### Completion-report schema

The Worker contract's report, plus: for Part 0, the before and after text; for
Part A, per source family what was searched and found, a separate conclusion
for each of the two mechanics at the confidence the evidence supports, and any
recommendation for a later profile round; and every changed record's base and
head versions side by side.
