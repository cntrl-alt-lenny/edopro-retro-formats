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
ran in Brain's shared checkout again (the sibling worktree existed by
round 3 as a result) -- not a quality issue with this round's work, but
the reason the worktree convention needs the human to actually point a
local Worker session at `edopro-retro-formats-worker` for it to help.
