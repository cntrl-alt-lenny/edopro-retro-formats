# Active brief

Status: **accepted** (third delivery; see Outcome).

Identifier: **`023-2026-09-21-citation-registry-check`** — use exactly this
string as `--task` for every `tools/report.py` call in this round.

<!-- Brain bookkeeping (not part of the brief): one brief lives here at a
time; on adjudication move this file to
docs/briefs/archive/<NNN>-<date>-<slug>.md (022 is the latest archived) and
replace it with the next one. -->

## Read before acting

1. [`AGENTS.md`](../../AGENTS.md) — invariants, especially "prefer a mechanism
   over a list" and "provenance is mandatory".
2. [`docs/agents/roles/worker.md`](../agents/roles/worker.md) — your contract
   (the Builder holds the Worker contract).
3. This brief in full.
4. `data/sources.json` and how `retroformats/validate.py` already checks source
   references (`sources.missing` and related codes), so the new check fits the
   project's existing conventions.

Do not read `docs/research/` for content; this round treats it as input to a
check, not as material to review.

---

## MODE: IMPLEMENTATION

## Goal

A citation to an external source in the project's research material cannot be
added without a matching record in `data/sources.json`, and a test fails when
one is. Citations that already lack a record are listed explicitly as a
backlog that can shrink but never grow.

## Why this is next

Twice in five rounds a research change cited a source with no registry record,
and each time it cost a full correction cycle (rounds 18 and 22). `AGENTS.md`
already states the rule; the rule alone did not prevent it. The project's own
discipline is to prefer a mechanism over a list.

Brain's rough count at the base: of about 81 distinct URLs cited in
`docs/research/*.md`, about 61 appear nowhere in `data/sources.json`. That
count is a starting estimate, not a specification — establish the real figure
yourself.

## Base

Cut from `origin/main`. Record the literal starting SHA.

## Required investigation

1. **Define "cited" and "registered" precisely, and justify the definitions.**
   Decide which files are in scope (research Markdown only, or research JSON
   packets too) and say why. Decide how a citation matches a record: exact URL,
   normalised URL, an archived-capture URL whose original matches a record, a
   record that lists several URLs, and so on. A definition that is too loose
   lets unregistered sources through; one that is too strict floods the
   backlog with noise. Say which you chose and show examples of both kinds of
   error you avoided.
2. **Establish the real backlog** under your definition, and characterise it:
   roughly how many are archived captures, official pages, community pages,
   internal links, and anything that is not really a source citation.
3. **Decide what counts as a legitimate exemption** — for example a URL that is
   an example rather than a citation — and make exemptions explicit and
   reasoned, never implicit.

## Scope

- A check, runnable on its own and wired into the test suite, following the
  pattern of the project's existing generated-state checks.
- A committed backlog file listing today's unregistered citations, with the
  test failing if an entry is added to it, and passing when entries are
  removed (the ratchet).
- Tests proving the check fails on a new unregistered citation, fails when the
  backlog grows, passes when a backlog entry is registered and removed, and
  passes on the current tree.

## Non-goals

- **Do not register the backlog.** Clearing it is research work — each record
  needs a statement of what the source does and does not establish — and
  belongs in later rounds. This round only makes the backlog visible and
  closed to growth.
- Do not edit research documents or source records, except a genuinely
  malformed citation that cannot be parsed, and then report it.
- No validator finding code, severity or condition change: this is a test-suite
  check, not a new validation rule, unless you conclude it belongs in the
  validator — in which case stop and say why.
- No CI workflow change is needed; the suite already runs in CI.

## Protected invariants

- The check must be able to fail. Show it red on a deliberately planted
  unregistered citation and on a deliberately grown backlog, then green.
- A backlog that can silently grow is no guard. Prove it cannot.
- Validator baseline 0 errors, 569 warnings; GOAT hash `0x28E9FC02`; no
  canonical data or `dist/` change.
- Gates green at your head, CI included. If a gate cannot pass within the
  brief, stop and report; never bypass a check.

## Acceptance criteria

- The definitions of "cited", "registered" and "exempt" are written down next
  to the check, with the reasoning.
- The real backlog count and its characterisation are in the report.
- The four red/green demonstrations above, with real output.
- The suite passes at your head; CI green.

## Required evidence

`python -m unittest discover -t . -s tests -v`, `python -m retroformats
validate` and `python -m retroformats build --check`, with real output and exit
status, on Python 3.10 or newer; the check's own output on the current tree;
and each red/green demonstration.

## Git expectations

Work only in `.worktrees/builder/`; every file you create or edit must be
inside it. Branch `builder/citation-registry-check` from `origin/main`.
Focused commits; push the branch; never push `main`; never merge; never bypass
a local check. Before finishing, run
`git -C /Users/leo/Dev/edopro-retro-formats status --short` and confirm it
prints nothing. After your final commit and push, write your report from
inside `.worktrees/builder/` with
`python3 tools/report.py write --task 023-2026-09-21-citation-registry-check`
(Python 3.10+), as well as displaying it.

## Completion-report schema

The Worker contract's report, plus: the three definitions and why; the real
backlog count and characterisation; each red/green demonstration; and anything
the check deliberately does not catch, stated plainly.

---

## Amendment 1 — 2026-09-21, after Brain's first adjudication

The first delivery, `2160e9b1c063af585aa4c2626d653eff909bbd0d` on
`builder/citation-registry-check`, was **not accepted**. Most of it stands and
is not reopened: the scope (`docs/research/**/*.md` and `.json`), the URL
normalisation and archived-capture matching, the 110-entry backlog (the
Verifier's independent scan found the same 110 keys; Brain's earlier "about 61"
was a Markdown-only estimate), and the ratchet against a growing backlog.

Continue on the same branch from `2160e9b`; do not rewrite history. This
amendment lives on `origin/main`: read it with
`git show origin/main:docs/briefs/active.md`.

### The guard has a side door

An exemption is meant to apply to specific occurrences — the redirect
destinations quoted in `docs/research/edison-behaviour-gaps.md`. The
implementation records the exemption once per normalised URL, from whichever
occurrence is scanned first, so every other occurrence of that URL in any
research file inherits it. Brain reproduced this on a copy of the delivered
head: appending `http://www.yugioh-card.com/en/` to
`docs/research/edison-rules.md` leaves the test green, while appending a
genuinely new unregistered URL turns it red.

Make exemptions apply per occurrence — file and location — so an exempt use in
one place never licenses an unregistered use elsewhere. Add a test that plants
exactly this case and fails before your fix, and show it red on the current
code and green after.

**Then look for the same class.** Anything else in the check that is decided
once per URL but should depend on where the URL appears — backlog entries,
registry matching, anything keyed on the deduplicated URL — say whether it has
the same flaw, and fix or justify each.

### Unchanged

Everything else in the brief, including not registering the backlog and not
editing research documents or source records. The report covers the whole
round from base `f518cc3b8f4a773e07f8bcf54de90331f7377254`, and states plainly
anything the check still does not catch.

---

## Amendment 2 — 2026-09-21, after Brain's second adjudication

The second delivery, `0141962f049858328d3d85ced04da4fe0802d1b9`, was **not
accepted**. The cross-file leak is fixed and stays fixed; the backlog, ratchet
and everything else Amendment 1 said stands still stand.

### The exemption is scoped to a file, not a location

The redirect-destination exemption now checks only that the occurrence is in
`docs/research/edison-behaviour-gaps.md`. Any use of those URLs anywhere in that
file is exempt. Brain reproduced this on a copy of the delivered head: appending
"We cite http://www.yugioh-card.com/en/ as the source for this claim." to that
file leaves the test green. Amendment 1 asked for exemption by file **and
location**.

Requirements for the fix, stated as constraints rather than a design:

- An exemption must apply only to the specific occurrences it was reasoned for,
  and must not license any other occurrence of the same URL, in the same file or
  elsewhere.
- It must survive unrelated edits to the file. Line numbers alone will not:
  adding a paragraph above the table would silently break or move them.
- It must be visible and reviewable at the occurrence, so a reader of the
  research document can see that a URL is deliberately exempt and why. This
  repository already has a precedent for an explicit, reviewable exemption
  marker in normative text: the `guard:counterexample` blocks used in
  `docs/agents/git-and-isolation.md`. Follow that spirit or justify something
  better.
- If the fix needs a marker inside the research document, that edit is
  authorized for exactly the exempt occurrences, and nothing else in the
  document changes.

Tests: plant this round's case (the exempt URL at a new, unrelated location in
the same file) and show it failing on the current code, then green; keep the
cross-file test; and add a test that an unrelated edit elsewhere in the file
does not break the legitimate exemption.

### Unchanged

Everything else. Continue from `0141962`; do not rewrite history. The report
covers the whole round from base `f518cc3b8f4a773e07f8bcf54de90331f7377254`.

---

## Outcome — accepted 2026-09-21 on the third delivery, merged with owner approval

Head `a271d4378f1b85f23e9c48c720d94f760c71fb08`, base
`f518cc3b8f4a773e07f8bcf54de90331f7377254`.

**Result.** The test suite now fails when `docs/research/**/*.md` or `.json`
cites an external URL with no matching `data/sources.json` record (normalised
URL or archived-capture original). Today's 110 unregistered citations are a
committed backlog that may shrink but not grow. Exemptions are explicit
`citation-exempt` markers at each exempt occurrence, with a reason.

**Returns.** First delivery: an exemption meant for one file applied to the
URL in every file. Second: scoped to a file but not a location — **partly
Brain's defect**, since "file and location" was loose enough to be read as
"file". Amendment 2 stated the requirement as testable constraints, and the
third delivery met them.

**Brain re-derived**, on a copy of the head: the second delivery's bypass now
fails; an unrelated edit above the table leaves the legitimate exemptions
passing; the research document is byte-identical to base with the markers
stripped.

**Known, documented limit:** a copied marker is trusted; it is visible in
review, the same trade-off as `guard:counterexample` blocks.

**Backlog:** 110 citations to register in later rounds, each with a statement
of what the source does and does not establish.
