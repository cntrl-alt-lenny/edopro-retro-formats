# Model notes

A running, dated log of what's actually been observed about running
Worker on different models — kept separate from `AGENTS.md` so that file
stays lean and doesn't accumulate model-specific trivia that goes stale.
Only record things actually observed in a real round here; don't
pre-populate with generic advice this project hasn't earned yet.

Worker is explicitly model-agnostic (see `AGENTS.md`) — this file is
supporting evidence for that design, not a ranking. Brain's review
standard (independently re-check everything) does not change based on
which model executed a round.

## Round log

**Round 1 (2026-08-30) — Tokyo Dome epistemic-wording fix
(`docs/briefs/archive/001-2026-08-30-tokyo-dome-epistemic-wording-fix.md`),
model: a non-Claude frontier model ("GPT 5.6 Luna" per the human's
description), effort: High.** Accepted without correction. Findings: did
the full re-grep the brief asked for rather than stopping at the listed
instances (caught one the brief's own list missed:
`phase_g_content_completeness_result`); preserved the `evidence_tier`
data-field's leading-number/slug shape exactly as instructed; confirmed
the JSON-key rename it made wasn't referenced anywhere else before doing
it, matching the brief's own required check. One operational note, not
about model quality: it ran directly in Brain's own local checkout and
left it on its work branch, which Brain didn't notice before committing
unrelated work on top — this is what
`docs/agents/worktree-mechanism.md` (added the same day) exists to
prevent going forward, not a defect in this round's actual output.

**Round 3 (2026-08-31) — April 2005 (GOAT) banlist import + verification
(`docs/briefs/archive/003-2026-08-31-april-2005-goat-banlist-verification.md`),
model: Claude Sonnet 5 High, in the sibling worktree (first round to
actually use it -- no collision this time).** Accepted without
correction. Ran the importer for the first time against Yugipedia's
"April 2005 Lists" page, correctly caught that the page has no "(TCG)"
suffix unlike the March 2010 precedent (didn't just assume naming
consistency). Independently found and correctly resolved a real
discrepancy the brief didn't anticipate: `docs/edopro-research.md`'s
pinned BabelCDB revision (`da54f28`) is stale relative to
`data/sources.json`'s own `ignis-babelcdb` entry (a newer revision) --
used the canonical data file, not the doc, and said so explicitly. Went
beyond the brief's minimum bar: independently re-fetched two period
primary sources Yugipedia's own page cites (an Upper Deck Entertainment
tournament-policy document and a Pojo.com page Wayback-archived three
weeks before the list's effective date) rather than resting the
`verified` upgrade on Yugipedia alone. Brain independently re-fetched one
of those two sources (the Pojo.com page) directly and confirmed the
17/41/15 counts and effective date match exactly, rather than trusting
the report. Correctly left `superseded_by_date` unresolved (still not
primary-sourced) and `format.json`'s `implementation_status.banlist`
untouched, re-checking the code-linkage question fresh rather than citing
round 2's finding as an assumption.

**Round 2 (2026-08-30) — March 2010 banlist verification
(`docs/briefs/archive/002-2026-08-30-march-2010-banlist-verification.md`),
model: Claude Sonnet 5, effort: High.** Accepted without correction.
Independently re-derived the underlying claim, not just the diff: fetched
the same archived Konami page itself (via the browser tool -- WebFetch
refused `web.archive.org` directly, same limitation Worker's report
noted) and programmatically diffed its 132 named cards against the JSON's
`entries` array -- exact match, zero cards only on either side, zero
status mismatches, confirming Worker's claim rather than just trusting
its report. Also independently caught and corrected an error of Brain's
own: the brief said "46 entries" (an unverified guess from skimming the
file's head/tail) when the real count is 132 -- Worker counted correctly
from the actual data rather than anchoring on the brief's wrong number.
Correctly left `formats/2010-03-edison/format.json`'s own
`implementation_status.banlist` untouched per the brief's non-goals,
having confirmed (and Brain independently re-confirmed via
`retroformats/validate.py`) that field isn't code-derived from the
banlist file's own `completeness`. Same operational note as round 1:
ran in Brain's shared checkout again (the nested worktree existed by
round 3 as a result, and round 3 was the first to actually use it,
cleanly) -- not a quality issue with this round's work, but the reason
the worktree convention needs the human to actually point a local Worker
session at the nested worktree for it to help. (The worktree's own
location changed again after round 3 -- from a Dev/-level sibling folder
to `.claude/worktrees/worker/` nested inside the single project folder,
per the human's explicit preference; see
docs/agents/worktree-mechanism.md.)
