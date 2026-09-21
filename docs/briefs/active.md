# Active brief

Status: **queued, not started**.

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
