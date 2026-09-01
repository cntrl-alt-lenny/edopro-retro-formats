# Active brief

Status: **complete** — landed as `f355d79`, reviewed and merged 2026-09-01.

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
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: HISTORICAL RESEARCH

Read that mode's rules carefully before starting. In particular:
**canonical data and schema changes are forbidden this round** except
where Part A explicitly authorises a documentation fix. Findings are
recorded in `docs/research/`; applying them to the 68 affected errata
records is a separate, later DATA round.

## Goal

Roadmap item 1b — **close, or narrow, the failed-search deck-verification
interval.**

This is the highest-leverage open chronology question in the project, and
the reason is sharper than the roadmap states. Brain measured it;
**re-derive it yourself rather than trusting these numbers**:

| format | snapshot | interval records ambiguous | determinate |
|---|---|---|---|
| `2005-04-goat` | 2005-04-01 | 48 | 20 |
| `2010-03-edison` | 2010-04-24 | 48 | 20 |
| `2011-09-tengu` | 2011-09-17 | **68** | **0** |

68 of the 296 errata records cite both bounds. Tengu — the newest
canonical format — sits inside the open interval on **every single one**.
GOAT and Edison are partly protected because their snapshots precede
`2011-02-02`, but even they are ambiguous on 48, which suggests a
*second* cause bundled into the same records (see Part B's note on
disentangling the two axes).

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean.

---

## Part A — a conflation round 9 found but correctly left alone

Round 9 established, from `gframe/data_manager.h` at the pinned
`edopro-source` revision, that `SCOPE_PRERELEASE` (`0x100`) is an **`ot`
bit-flag**, not a passcode range. The prerelease *passcode* convention is
a separate thing (`10ZZYYXXX`, per BabelCDB's own README).

Round 9 fixed `docs/roadmap.md`'s wording but deliberately did not touch
the research corpus. Check whether `docs/research/ignis-goat.md` and
`docs/research/edopro-data-repos-ui.md` carry the same conflation, and
correct it where they do — citing the pinned revisions, not this brief.

If they are already correct, say so plainly; "nothing to fix" is a fine
result. Do not rewrite either document beyond this specific point.

---

## Part B — the interval (the substantive part)

### What is currently established

From `docs/errata.md` § "What the research established" (read it, and the
records themselves, rather than relying on this summary):

- The old procedure — Project Ignis encodes it as `Duel.GoatConfirm` —
  was official TCG ruling-layer policy through at least **2011-02-02**
  (Konami's Storm of Ragnarok rulings).
- The modern no-verification policy is first attested **2019-04-03**.
- No announcement of the change has been found, so the chronology is
  recorded as a bounded interval rather than a date.

### The question

**When did the TCG stop requiring a player to reveal their Deck to verify
a failed search?**

Any genuine narrowing helps. The single most valuable result is evidence
either way about **2011-09-17**, Tengu's snapshot — because that one date
flips 68 records from ambiguous to determinate for that format.

Note carefully what each outcome would mean:

- Evidence the **old** state still held after 2011-09-17 → Tengu resolves
  to the old era, like GOAT and Edison.
- Evidence the **new** state was already in force by then → Tengu resolves
  to the modern era, which is a materially different format.
- Evidence narrowing the interval but not past that date → still valuable;
  record it.

Do not let the convenience of the first outcome shape the reading of a
source. State what each source actually establishes.

### Where to look

The existing research names the shape of source that has worked before:
period Konami/UDE rulings documents, per-set rulings PDFs, judge-list
archives, and official Card FAQ captures. Candidate leads, none
guaranteed:

- Konami TCG rulings documents for sets between 2011 and 2019, the same
  series as the Storm of Ragnarok document already cited;
- archived `yugioh-card.com` rulings/FAQ pages via the Wayback Machine —
  the same technique that produced round 2's and round 6's primary
  sources;
- Konami's published tournament policy documents, which
  `data/sources.json` already carries one 2011 example of
  (`konami-tcg-tournament-policy-v11-2011`);
- the transition to the "Problem-Solving Card Text" era and the 2019-era
  rulings-portal change, working *backwards* from the 2019-04-03
  attestation.

### Disentangling the two axes

`docs/errata.md` records a **second, separate** question in many of the
same records: whether a card could be *activated at all* with no valid
target, which changed **per card** and is dated for some (Reinforcement
of the Army by 2008-12-15) and unresolved for others.

Roadmap 5c already found these two axes are bundled in one upstream
script for a large cluster and cannot be sequenced against each other.
Establish which axis is responsible for GOAT's and Edison's 48
ambiguities, since it is evidently not the verification axis for them.
That is a real finding either way and it tells a future round where the
remaining work actually is.

Do **not** attempt to resolve the per-card activation axis this round —
that is roadmap 1a and is explicitly out of scope.

### A null result is a real result

The roadmap already records that no announcement was found. If this round
also fails to narrow the interval, that is an acceptable outcome — but it
must not read as "nothing happened."

Record, in the relevant `docs/research/` file: exactly which sources were
searched, how, what was and was not found, and what the failed search
does and does not prove. `AGENTS.md` is explicit that failing to find a
source is evidence about the search performed, never proof of global
non-existence. A future round must be able to see what has already been
tried and not repeat it.

## Non-goals

- Do not modify any `data/errata/*.json` record, even if you narrow the
  interval. Report the finding; applying it across 68 records is a
  separate DATA round with its own review.
- Do not change any format, pool, banlist, rule profile, or schema.
- Do not attempt to resolve the per-card activation axis (roadmap 1a).
- Do not attempt to run, install, or screenshot EDOPro (standing
  boundary since round 7).
- Do not add a dependency; standard library only.

## Protected invariants

- Canonical data (`data/`, `formats/`) is **unchanged** this round —
  `git status` must show no modification under either.
- All three generated lflists byte-identical; `dist/` unchanged.
- `python -m retroformats validate` stays at **0 errors**, warnings 569.

## Required investigation

1. Re-derive the ambiguity table above yourself.
2. Read what the 68 records actually encode for this axis before
   searching — the shape of the recorded chronology tells you what a
   useful source would have to say.
3. Search for period evidence, recording the search as you go.
4. Establish which axis drives GOAT's and Edison's 48 ambiguities.

## Acceptance criteria

- A definite statement of whether the interval narrowed, and if so, to
  what, with sources that meet this project's bar for the claim being
  made.
- If it did not narrow: a recorded, specific account of what was searched
  and what that does and does not prove.
- A definite answer on which axis causes GOAT's and Edison's 48
  ambiguities.
- Part A resolved, or a plain statement that nothing needed fixing.
- Canonical data and `dist/` unchanged; validator and full suite pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

Plus `git status --short data/ formats/ dist/` showing no changes.

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/search-verification-interval`). Do not merge to `main`
yourself. Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: what you found in each of the two research docs, and what you
  changed.
- Part B: the ambiguity table as you re-derived it; every source you
  searched and what each did or did not establish; whether the interval
  narrowed and to what; your evidenced answer on which axis drives the
  GOAT/Edison ambiguities.
- What a failed search does and does not prove, stated explicitly if you
  did not narrow the interval.
- Exact output of the three validation commands plus the `git status`
  check.
- Anything left genuinely uncertain, stated as uncertain.
