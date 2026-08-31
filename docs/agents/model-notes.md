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

**Round 9 (2026-08-31) — reserved passcode range, unblocking roadmap
item 7 (`docs/briefs/archive/009-2026-08-31-reserved-passcode-range.md`),
model: Claude Sonnet 5 High, in the nested worktree.** Accepted. The most
thorough evidence-gathering of any round so far.

Went well past the brief's scope on the survey: the brief described two
cdb files; Worker downloaded **all thirteen** in BabelCDB at the pinned
revision and queried them directly, including the `cards.cdb` the brief
admitted Brain had not checked. It then did the thing that actually makes
the choice defensible — fetched BabelCDB's **own README** at that
revision to separate *documented convention* (`10ZZYYXXX`, `160ZYYXXX`,
`30ZYYYXXX`, `511YYYXXX`) from *observed occupancy*, correctly treating a
conventionally-reserved-but-empty range as unavailable.

Corrected the roadmap's own wording on a real conflation: "prerelease
ranges" merges a passcode range with `SCOPE_PRERELEASE` (`0x100`), which
is an `ot` bit-flag and not a range at all.

Found and fixed a second, independent error the brief did not anticipate:
roadmap item 1c's "48 acknowledged implementation gaps" was stale. The
care here is the notable part — rather than just changing 48 to 41, it
established that **48 is itself a real figure for a different metric**,
so the original number was a conflation of two true counts rather than a
typo.

Brain verified independently rather than reading the diff: re-surveyed
all 13 cdbs at the pinned revision and reproduced every figure exactly —
24,702 unique passcodes, range 301–810000114, `cards.cdb` max 99995595,
and **zero codes in 600000000–699999999**; fetched BabelCDB's README and
confirmed all four documented conventions are real (and that `5047` is
*not* README-documented, which Worker correctly treated as observed-only);
and negative-tested the new rule by injecting `600000042` into a pool and
watching `card.reserved-passcode-collision` fire.

On the 41/48 correction Brain's first quick count disagreed, then proved
to be Brain's own sloppy derivation. Computed properly with the same
logic `report` uses: divergence union across all three formats = **41**,
known-wrong union = **48**, combined = **89** — every one of Worker's
three figures exact. Worth recording as a caution: a crude grep is not a
re-derivation, and nearly produced a false accusation.

One observation neither side raised: the 9xx decade is *also* empty and
would have served equally. Worker's claim was scoped to decades 0–8 and
is true as written, and 6xx is a fine choice — no defect, just noting the
choice was not forced.

**Sequencing consequence discovered after the merge:** item 7 still
cannot start. There are **zero `custom-script` coverages** in the corpus
(231 reuse-upstream, 56 known-gap, 4 none-needed), so the generator has
no input. Reserving the range first was still correct — it is expensive
to change later — but building the generator now would be speculative
machinery, so round 10 goes to chronology instead.

**Round 8 (2026-08-31) — deck validation tool, roadmap item 6
(`docs/briefs/archive/008-2026-08-31-deck-validation-tool.md`), model:
Claude Sonnet 5 High, in the nested worktree.** Accepted. The first
round to add a real user-facing feature rather than data or documents,
and the second consecutive round to correct its own brief.

Honoured the round's load-bearing constraint without being pushed:
`check_deck()` calls `build_lflist(fmt, repo).entries` — the same
function that produces `dist/lflists/` — so the checker cannot disagree
with the shipped artifact by construction. No `lflist.py` refactor was
needed at all; the four functions it reuses were already public. Zero
canonical data and zero `dist/` changes.

Corrected the brief's `.ydk` description by reading the pinned client
source (`deck_manager.cpp` @ `9d6fb3e8417c88`) rather than assuming:
there is no `#main` handling whatsoever (only the literal `#extra` line
matters), and *any* `!`-prefixed line switches to the side deck since
the parser never inspects the text after `!`.

Implemented the alias semantics faithfully to the cited source rather
than plausibly: counting merges under the alias root unconditionally,
while the *limit* lookup falls back to the alias only within the ±10
artwork range on a whitelist — which is exactly what
`LFList::GetLimitationIterator` does. Getting this backwards would have
made pre-errata identities silently legal.

On `forbidden_card_types` it neither faked the check nor silently
skipped it: it proved redundancy structurally from release dates and
printed a standing disclosure on every run.

Brain verified independently rather than reading the diff: fetched
`deck_manager.cpp` at the pinned revision and confirmed `LoadCardList`
matches every parsing claim; checked the `GetLimitationIterator` source
quoted in `edopro-lflists.md` against `_limit_for`'s implementation;
re-derived the Xyz first-printing dates from this repo's own release
records (2011-07-08 EU / 2011-08-12 EU — both after Edison's cutoff,
before Tengu's); ran the tool on all six fixtures; and independently
constructed fresh decks straight from the shipped Tengu and Edison
lflists, confirming both validate clean. An adversarial deck Brain built
also surfaced the alias merge working correctly in the wild — Jinzo
`77585513` plus artwork variant `77585514` counted together against a
limit of 1. 961 tests at the exact final SHA `197a28b`.

**One over-generalisation, sent to round 9** (it is user-facing output
text carrying an evidential argument, so not Brain's to reword): the
disclosure says the check is redundant because "its release-cutoff pool
cannot contain" a forbidden type — true for Edison and Tengu, but GOAT's
pool is `kind: extensional` with no cutoff at all. The conclusion holds
for GOAT by a different route; only the stated reason is wrong.

**Round 7 (2026-08-31) — ship as an EDOPro repo, roadmap item 8
(`docs/briefs/archive/007-2026-08-31-ship-as-edopro-repo.md`), model:
Claude Sonnet 5 High, in the nested worktree.** Accepted. Notable for
being the first round to **correct the brief itself** on a matter of
substance.

Brain's brief asserted that an unresolvable code on a whitelist
"silently removes a card." Worker checked rather than accepted it: the
brief pointed at `edopro-data-repos-ui.md`, which does not cover the
question, so it went to the sibling `edopro-lflists.md` §6.1 and found
the actual mechanism — an unknown code is flagged `DeckError::UNKNOWNCARD`
at deck-load time, *before* the whitelist check runs, and the whole deck
submission is rejected with a typed error naming the code
(`generic_duel.cpp:375-377,423,384-390`). That is a hard, visible
failure, not a silent one; Worker corrected the framing in
`dist/README.md` rather than repeating Brain's wording.

It also exceeded the brief's expectations on rigour in two places. The
brief allowed a partial upstream check; Worker did an exhaustive one —
downloading the real `goat-entries.cdb`/`cards-unofficial.cdb` from
BabelCDB at the exact pinned revision and querying them with stdlib
`sqlite3`. And on "does a default install already have this data", it
declined the easy "yes": it found DeltaBagooska's git-hosted deltas
carry only 5 of the 226 codes, leaving 221 dependent on an
already-recorded, still-unverified assumption about base-installer
contents — and labelled its own DeltaBagooska check as an unpinned live
snapshot rather than a reproducible citation.

Correctly refused the out-of-scope live client test and stated, in the
report and in `dist/README.md`, exactly what remains unobserved.

Brain verified independently rather than reading the diff: re-derived the
per-list counts from `dist/lflists/` (209/67/46, union 226); downloaded
both cdbs at the pinned revision and confirmed all 226 resolve — 191 in
`goat-entries.cdb`, 35 in `cards-unofficial.cdb`, zero overlap, every one
`ot=8`, none missing; read the `UNKNOWNCARD` citation and confirmed it
says what Worker claimed (so Brain's brief was wrong, not Worker);
verified the MR1/MR2/GOAT flag composition against the actual
rule-profile records, confirming Tengu's profile is bit-for-bit MR1 and
that the previous "Master Rule 2" instruction really would have omitted
`DUEL_OCG_OBSOLETE_IGNITION`; confirmed the "OCG Ignition Priority"
checkbox label and `0x100` mapping against the cited §4c; and re-ran 948
tests at the exact final SHA `5750b81`.

Worker also flagged, without touching it, that
`docs/research/ocgcore-flags.md` says GOAT is "MR1 | 12 extra flags"
while the data shows 11. Brain confirmed the doc's own hex in the same
sentence (`0x7F800002C`) has exactly 11 set bits, making it a
self-contradicting typo rather than an adjudication, and fixed it
directly as trivial housekeeping.

**Round 6 (2026-08-31) — Tengu `legality_basis` + banlist source
verification + stale-source sweep
(`docs/briefs/archive/006-2026-08-31-tengu-legality-basis-and-banlist-evidence.md`),
model: Claude Sonnet 5 High, in the nested worktree.** Accepted. The
strongest round yet on evidence discipline, with one wording defect
carried into round 7.

Part B was the piece that mattered. The brief framed "can Tengu's
banlist reach `verified`?" as a genuine question with "no" explicitly
allowed. Worker falsified the existing primary citation rather than
leaning on it: `konami-september-2011-list` is Konami's *Japan-domain
OCG* regulation page, and its English column is a translation aid, not
independent TCG evidence — proven by a forbidden entry (Sixth Sense)
whose TCG-name cell is blank. It then found a genuine period-archived
TCG-side page (`yugioh-card.com/en/limited/`, Wayback 2011-09-23, same
page family as Edison's accepted precedent) and reconciled against that
instead. It also distrusted its own tooling: a WebFetch summary claimed
the Japan page had no TCG column at all, which was flatly wrong, and
Worker re-verified by direct inspection rather than reporting the
summary. That instinct is the reason this round is trustworthy.

Two other things done right: it flagged unprompted that adding
`legality_basis` to `schemas/pool.schema.json`'s `required` array has
**zero enforcement effect**, because nothing in this repo runs a generic
JSON-Schema validator over pools — so the real fix is the `validate.py`
change alone. And it did a real red/green cycle on the new rule rather
than asserting one.

Brain verified independently rather than reading the diff: fetched the
archived Konami page directly and re-derived the entire reconciliation
from raw HTML — 134 page entries vs 134 JSON entries, 51/65/18 both
sides, zero cards on either side only, zero status mismatches, exact
match after normalising the page's full-width hyphens; confirmed the
page's own "Effective September 1, 2011 / UPDATED: 8/18/11" text;
negative-tested `pool.missing-legality-basis` by deleting the field and
watching validate go to 1 error, then restoring; confirmed no
`jsonschema` import exists anywhere and `tests/schema_check.py` is wired
only to `erratum.schema.json`, so the zero-enforcement disclosure is
accurate; and re-ran 947 tests at the exact final SHA `a81ca09`.

**The one defect, sent to round 7 rather than fixed by Brain** (it is
canonical data and an evidence claim, which the operating policy keeps
out of Brain's hands): the note asserts Sixth Sense has "no TCG printing
at all" — a universal negative that nothing cited establishes, and that
this repo's own TCG coverage (ending 2011-09-17) cannot reach. Yugipedia's
card page shows an empty `en_sets`, so the claim is probably true, but
probably-true-and-unsourced is exactly what this project's bar excludes.
The argument it supports is sound on the weaker period-scoped claim, so
the conclusion stands and only the sentence needs correcting.

**Round 5 (2026-08-31) — status propagation / axis-drift audit /
BabelCDB revision honesty
(`docs/briefs/archive/005-2026-08-31-status-propagation-consistency.md`),
model: Claude Sonnet 5 High, in the nested worktree.** Accepted without
correction. First deliberately *bundled* round under the 2026-08-31
operating policy (three related parts, one briefing, one review) — the
bundling worked: no part was starved, and review cost was well under
three separate rounds.

Did not simply apply the brief's predicted upgrades: read the two
banlists' own recorded evidence first and argued each against
`implementationStatus`'s `verified` wording before changing anything,
and correctly left Tengu alone. On `overall`, established there is no
derivation rule anywhere (validator only enum-checks; `cli.py` and the
atlas generator print the stored value) and left both at `partial`
because `rule_profile` is the real bottleneck — the conservative
direction, which is the right one under "statuses are earned, never
aspirational."

Part C was the strongest piece: took the honest option (freeze the
verification claim to the revisions actually checked, flag that
`ignis-babelcdb` has since moved, and state plainly that the
BabelCDB-derived claims have *not* been re-verified), and explicitly
scoped round 4's inspection of the new revision as evidence about two
passcodes rather than a re-verification. That is exactly the
publication-date-is-not-effective-date discipline this project exists to
enforce.

Brain verified independently rather than reading the diff: re-derived
all six revision pins from `data/sources.json` (five match, only
BabelCDB drifted — as claimed); traced the BabelCDB pin move to
`0f65c3b` "Extend TCG release ledger through Tengu snapshot", confirming
Worker's "for reasons unrelated to this document" is a fact rather than
a guess; re-ran validate/`build --check`/946 tests at the exact final
SHA `bcc9b6f`; and confirmed the SVG diff touches only the `data-banlist`
attribute, the banlist swatch colour, and the banner tooltip, with the
visible "Partial" overall label unchanged.

One claim Brain re-derived by a route Worker did not state: GOAT's
banlist notes admit `superseded_by_date` (2005-10-01) is sourced only by
Yugipedia's convention, not primary evidence — a known gap that could
have blocked `verified` (which requires `complete`, which requires
"known gaps resolved or proven harmless"). It is provably harmless *at
this format's snapshot*: `validate.py`'s check is `snapshot >=
superseded`, GOAT's snapshot is 2005-04-01, and the list took effect
that same day, so no value later than the effective date changes the
outcome. The upgrade holds — but Worker reached the right answer without
addressing the field, so this was a real gap in its argument rather than
in its conclusion.

**Round 4 (2026-08-31) — Mind Master TCG/OCG card-identity gap, roadmap
1e (`docs/briefs/archive/004-2026-08-31-mind-master-card-identity.md`),
model: Claude Sonnet 5 High, in the nested worktree.** Accepted without
correction — the first round that was a design question rather than
verification, and the strongest so far.

Chose an explicit, sourced, per-instance mechanism
(`pool.cutoff.region_substitutions`, mirroring the existing
include/exclude idiom) over auto-discovery, and justified the refusal to
automate: direct inspection of the pinned BabelCDB found the OCG and TCG
Mind Master rows carry *functionally* different text, so silent
substitution could swap behaviour, not just region scope. That is the
right call under this project's historical-truth/representability
separation, and it is exactly the "don't ship a wrong general rule
silently" instruction the brief gave.

Went beyond the brief in two useful ways: replaced the test-only
allowlist with a real, pool-kind-agnostic validator error
(`pool.card-region-scope-mismatch`), so the *class* now fails
`validate()` until adjudicated rather than being pinned by one test; and
found a second, dormant instance of the same BabelCDB pattern (Elder
Entity Norden) not referenced by any current format. It also corrected
the roadmap's own description of the root cause — the TCG row is in
`cards-unofficial.cdb`, not `cards.cdb` as the roadmap assumed.

Brain verified independently rather than reading the diff: recomputed all
three lflist hashes from source (GOAT's `0x28E9FC02` unchanged, so Ignis
parity held), confirmed the `<10` artwork-window claim against
`validate.py`'s actual comparisons (so the `+10` offset genuinely needs
explicit listing), checked banlist statuses carried through the
substitution (Edison `1`/Limited, Tengu `0`/Forbidden — both preserved),
and negative-tested the new validator rule by reverting a pool entry and
confirming it errors. The one claim left unverified is the Elder Entity
Norden sighting, which needs a BabelCDB clone; it is informational and
affects nothing.

Process note: Worker branched from `8f8cf0f` while `main` advanced to
`b5b1795`, so the merge was a cherry-pick rather than a fast-forward.
Reviewed as `665325b`, landed as `e8ef36e`; `git patch-id` confirmed the
applied change is byte-identical to what was reviewed.

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
