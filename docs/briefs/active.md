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
   completion-report schema you must report back in.

Then this brief in full. Read only the further docs this brief scopes as
relevant — don't ingest `docs/research/` wholesale.

---

## MODE: DATA/SCHEMA

## Goal

Three related consistency defects, bundled into one round because they
share the same root shape: **work that was actually done is not reflected
in the records that report it.** Rounds 2 and 3 verified two banlists
against primary sources, but the formats' own status fields still
understate them, so `python -m retroformats report` and the generated
atlas both under-report the project's real state.

## Starting SHA

Verify with `git log -1` on `main` before starting; note the actual SHA
in your report. `main` should be clean — Brain stashed unrelated
in-progress work before queuing this.

## Why this is next

Roadmap items 2 and 3 are done (rounds 3 and 2). This round closes the
loop on them rather than starting something new, and clears a
documentation drift that round 3 surfaced but was correctly out of scope
to fix at the time. All three parts are small; bundling them amortises
one briefing and one review instead of three.

## Part A — propagate the banlist status rounds 2 and 3 earned

Brain has already confirmed the exact current values, but **re-derive
them yourself rather than trusting this table**:

| format | `implementation_status.banlist` | its banlist file's `completeness` |
|---|---|---|
| `2005-04-goat` | `partial` | `verified` |
| `2010-03-edison` | `complete` | `verified` |
| `2011-09-tengu` | `complete` | `complete` |

The first two are understated. **Tengu's is correct and must not be
touched** — its banlist has never been through a verification round, so
`complete` is the honest value. Do not "helpfully" align it.

Update the two understated fields to `verified`. Before you do, satisfy
yourself that the evidence actually supports it at this project's bar
(`schemas/common.schema.json`'s `implementationStatus`: `verified`
requires corroboration by strong primary/period evidence, not modern
community consensus) — read what rounds 2 and 3 actually did, recorded in
`data/banlists/tcg/{2005-04,2010-03}.json`'s own `notes` and `sources`,
and in `docs/briefs/archive/002-*` and `003-*`. If you conclude either
does **not** meet the bar, say so and leave it — do not upgrade a status
just because this brief predicted you would.

Also determine whether `implementation_status.overall` should change as a
consequence. Find out whether `overall` has a defined derivation rule
anywhere (schema, validator, docs) or is a per-format judgement, and act
accordingly — don't assume it's the minimum of the other axes without
checking.

## Part B — audit the other axes for the same defect

Part A is one instance of a class: a status field that drifted from what
the underlying data supports. Check whether the same is true elsewhere.

Brain's read, again **to verify, not trust**: `card_pool` appears
consistent across all three formats (`complete`/`complete`,
`verified`/`verified`, `verified`/`verified`), and `rule_profile` and
`errata` have **no** mirrorable source — `schemas/rule-profile.schema.json`
defines no `completeness` field and the three rule-profile files carry
none, so those axes are adjudications rather than reflections.

Report what you find. If `rule_profile`/`errata` are genuinely
judgement-only, say so plainly — that is a useful finding, and it means
this class of drift is structurally limited to `banlist` and `card_pool`.
**Do not invent a `completeness` field for rule profiles** to make them
mirrorable; that would be a schema change well outside this brief.

If you find a *third* drifted field, report it before changing it.

## Part C — the stale BabelCDB revision

`docs/edopro-research.md`'s header states its claims were "confirmed
against source code at the pinned revisions recorded in
`data/sources.json`", then lists `BabelCDB da54f28`. But
`data/sources.json`'s `ignis-babelcdb` now pins
`0659607453a7d79d1adefbfe1ef7477d3c92434c` (retrieved 2026-08-27). The
other pins in that sentence (LFLists `98ecbfd`, CardScripts `383bfbd`)
still match — only BabelCDB drifted.

**Do not simply swap the string.** The sentence asserts the document's
claims were *verified against* those revisions. Replacing `da54f28` with
the current hash would silently assert a re-verification that nobody
performed — precisely the "publication date is not effective date" class
of error this project exists to avoid.

The honest fix distinguishes *when a claim was verified* from *what is
currently pinned*. Choose and justify one:

- record that the document's BabelCDB-derived claims were confirmed
  against `da54f28`, while canonical data now pins a later revision; or
- actually re-verify the BabelCDB-derived claims in that document against
  the current revision, and then update the string truthfully; or
- something better you can defend.

Option two is real work and may exceed what this round should carry — if
so, take option one and say why. Note that round 4 already inspected the
current revision for card-identity purposes, which is evidence about two
specific rows, **not** a re-verification of this document's claims.

## Scope consequence: the generated atlas

`implementation_status` feeds `scripts/generate_format_atlas.py`, so any
Part A change alters `docs/assets/format-atlas.svg` and
`format-banner.svg`. Regenerate them (`python scripts/generate_format_atlas.py`,
no flags — offline and deterministic) and commit the result;
`tests/test_format_atlas.py::test_checked_in_svg_is_fresh` fails
otherwise. Do **not** run `--refresh`, which re-pulls the live Format
Library catalog and is out of scope.

Expect the SVGs to change. Confirm the change is *only* the status
colours/labels for the fields you edited, and say so.

## Non-goals

- Do not touch banlist `entries`, pool `cards`, or any historical
  adjudication — this round changes status *reporting*, not evidence.
- Do not verify Tengu's banlist against primary sources. That is real
  work and deserves its own round; note it as a candidate if you like.
- Do not redesign the atlas or banner. Regenerate only.
- Do not add a `completeness` field to the rule-profile schema.

## Protected invariants

- All three generated lflists must be **byte-identical** after this round
  — nothing here should touch card resolution. Confirm via
  `build --check` and by checking `git status` shows no `dist/` change.
- GOAT's EDOPro content hash stays `0x28E9FC02`.
- `python -m retroformats validate` stays at 0 errors.

## Required investigation

1. Re-derive the status table in Part A yourself from the actual files.
2. Establish whether `overall` has a defined derivation rule before
   changing or not changing it.
3. Confirm `rule_profile`/`errata` have no mirrorable source, rather than
   taking Brain's word for it.
4. Check what the atlas SVG diff actually contains after regeneration.

## Acceptance criteria

- The two understated `banlist` fields reflect what the evidence
  supports, or a clear argument for why they should not.
- Tengu's banlist status unchanged.
- A definite answer on whether the drift class extends beyond `banlist`.
- `docs/edopro-research.md` no longer implies a verification that did not
  happen.
- `dist/` byte-identical; atlas regenerated and fresh.
- Full suite, validator, and `build --check` all pass.

## Tests / validation

Run and report exact output:

```
python -m retroformats validate
python -m retroformats build --check
python -m unittest discover -t . -s tests -v
```

## Git expectations

Work in the nested worktree (`.claude/worktrees/worker/`, see
`docs/agents/worktree-mechanism.md`) if running locally alongside a Brain
session. Fetch `origin/main` and branch from there
(e.g. `worker/status-propagation-consistency`). Do not merge to `main`
yourself. Do not push.

## Completion-report schema

Report:

- Starting SHA, branch, final SHA.
- Part A: the status table as you re-derived it, what you changed, and
  your reasoning on `overall`.
- Part B: whether the drift class extends beyond `banlist`, with
  evidence.
- Part C: which option you took for the BabelCDB drift and why.
- What the atlas SVG diff actually contained.
- Exact output of the three validation commands, plus confirmation
  `dist/` is unchanged.
- Anything left genuinely uncertain, stated as uncertain.
