# Edison card-behaviour triage (roadmap item 5c)

**Purpose:** turn the two headline errata-warning counts for the Edison format
into an exact, per-card remediation map, so future research/implementation
work can be pointed at the highest-leverage shared cause instead of at
individual cards one at a time. This is an audit only - no card behaviour,
selection logic, or historical implementation changes in this milestone.

**Method:** every figure below is recomputed directly from the project's own
selection model (`retroformats.model.Erratum.selection_at`), not from memory
or from an earlier summary of this project. The exact extraction script's
logic is described in "Reproduced state" below; its output was independently
cross-checked against `python -m retroformats report -v`'s own live counts
and matches exactly. Per-card root-cause classification and the qualitative
fields (behavioural difference, chronology/implementation blocker,
recommended action) were produced by an LLM workflow given ONLY the precise
structured facts already in this project's own `data/errata/*.json` records -
no new web research was performed for this milestone, and no field below
states anything the underlying erratum record doesn't already support.

**Revision note (two rounds).** The first version of this document
classified all 44 `format.erratum-modern-known-wrong` records as partition
**A** (chronology-only) using an "at least one candidate has a usable
implementation" test. Adversarial review found that test too weak against
the task's actual A/B/C definition, and found that `changes[]`'s
schema-documented "ordered oldest-to-newest" chain assumption does not hold
for a significant slice of the data. The first correction fixed the
A/B/C/D partition to A 0 / B 41 / C 44, but got two things wrong in the
process: it described the Giant Rat "candidate 1" semantics backwards
(inverting which joint state it formally represents), and it over-generalised
the "independent, unsequenced ruling axes" finding to all 44 known-wrong
records (flagging only Axe of Despair as an exception) when in fact only
**38** of the 44 - the entire failed-search/deck-verification cluster - are
genuinely independent-axis cases; the other 6 (Axe of Despair, Tyrant
Dragon, Vampire Lord, XY-/XYZ-/XZ- Dragon/Tank Cannon) are ordinary,
partially-dated linear chains. This second correction fixes the Giant Rat
semantics precisely (see "A/B/C/D partition"), establishes and reports the
independent-axis (38) vs. ordinary-linear-chain (6) split explicitly (see
"Independent-axis C vs. ordinary-linear-chain C"), corrects the resulting
38-card cluster's remediation direction, which had been described backwards
(see cluster 1 below), and corrects the roadmap-item attribution for the
cluster's open question (1a, not 1b). The corrected A/B/C/D counts (A 0 / B
41 / C 44) and the 44/41/85 headline counts are unchanged by this second
correction; the 41 divergence/B-partition records remain unaffected by
either correction.

## Reproduced state

Recomputed from HEAD via `python -m retroformats report -v` and a direct
query against `Erratum.selection_at()` for the Edison snapshot
(2010-04-24), cross-checked against `python -m retroformats validate`'s
warning counts:

| Category | Validator warning code | Count |
|---|---|---|
| Known-wrong modern fallback | `format.erratum-modern-known-wrong` | **44** |
| Acknowledged implementation gap | `format.erratum-known-divergence` | **41** |
| Overlap between the two | — | **0** (mutually exclusive by construction - see below) |
| **Unique affected cards (union)** | | **85** |

**A note on the "48" figure carried into this milestone's brief:** it is real,
but it is not the Edison-applicable acknowledged-gap count. `python -m
retroformats report -v`'s own summary line reports "48 unresolved" as a
**global, project-wide** count of `implementation.strategy == "unresolved"`
erratum records (`errata: 296 records ... strategies: 14 none-needed, 234
reuse-upstream, 48 unresolved`) - i.e. every card anywhere in the corpus whose
implementation strategy hasn't been decided, regardless of whether that
card's chronology even resolves to the unresolved version at the Edison
snapshot specifically. Filtering to just the 48 that are also selected as
applicable at Edison's exact snapshot date removes 7: one (Amazoness Fighter)
resolves to the **modern** version at Edison, so the missing historical
implementation is irrelevant there; six (Anteatereatingant, Armored Glass,
Dimension Distortion, Fushioh Richie, Metalsilver Armor, Spirit's Invitation)
have **ambiguous** chronology at Edison where the modern card itself remains
a possible candidate, so they are not confidently "known-wrong" or a
confirmed gap either - they surface instead as the weaker
`format.erratum-unresolved-defaulted` warning (part of a separate, larger,
genuinely-uncertain population of 106 records not addressed by this
milestone; see "Out of scope" below). 48 − 7 = 41, exactly matching the live
`format.erratum-known-divergence` count. The task brief's "92-row list"
estimate (44 + 48) is likewise corrected to **85** once the true, Edison-
specific figures are used.

**Overlap:** structurally zero. The two validator warnings come from mutually
exclusive branches of the same selection check
(`retroformats/validate.py:769-876`): `format.erratum-known-divergence` fires
only when chronology is fully **determinate** at the snapshot (state
`"gap"`); `format.erratum-modern-known-wrong` fires only when chronology is
**ambiguous** at the snapshot (state `"ambiguous"`) but the modern version can
be ruled out anyway. A record cannot be in both states at once. Verified
empirically as well as structurally: the id sets have zero intersection.

**Out of scope for this milestone** (context, not part of the 85): 72 records
already have working historical substitutions in force at Edison (no
problem); 12 resolve cleanly to the modern card (no problem); 106 more are
`format.erratum-unresolved-defaulted` - ambiguous chronology where modern
remains a *possible* candidate, so nothing is yet *proven* wrong. That 106-
record population is a distinct, larger research problem (whether modern is
actually correct for each one is simply unknown) and is not analysed further
here. GOAT format comparison, verified rather than assumed: GOAT's
`format.json` sets `errata_overrides.reference_parity` (not
`unresolved_policy`) - its REAL card substitutions come from matching Project
Ignis's own reference GOAT list, not from the chronology-driven
ambiguous/gap selection this document analyses for Edison; disagreements
with that reference are reported separately, via
`format.parity-omits-historical` (21) / `format.parity-substitutes-non-behavioural`
(11), not via the two codes this document covers. `report -v`'s own
"known-wrong"/"divergence" figures per format are computed by the SAME raw
chronology-selection logic for both formats regardless of reference_parity,
so GOAT's numbers there can be read as "what Edison-style selection would
say" rather than GOAT's real behaviour: under that computation, GOAT's
acknowledged-gap set is **the identical 41 cards** (same erratum IDs - these
implementation gaps are era-independent, not a coincidence), while GOAT's
known-wrong count is always zero not because its chronology differs, but
because GOAT's `format.json` sets no `unresolved_policy.choice` at all - the
`policy == "modern"` condition the known-wrong check requires can never be
satisfied for GOAT, independent of what the chronology says. Edison's pool
is 3,673 cards; the 85 affected cards are about 2.3% of it.

## A/B/C/D partition

Per the task's framework, stated precisely (the first pass used a weaker
proxy - see "What was wrong" below):

| Partition | Definition |
|---|---|
| **A. Chronology-only** | chronology unresolved, but *every* historically plausible outcome relevant to resolving the chronology is already implementable, so research alone can settle the card |
| **B. Implementation-only** | chronology determinate; the required version lacks an implementation |
| **C. Both** | chronology unresolved *and* one or more historically plausible candidate behaviours lack an implementation |
| **D. Other** | blocker is not an ordinary chronology/implementation gap |

| Partition | First-pass count | Corrected count |
|---|---|---|
| A | 44 | **0** |
| B | 41 | 41 (unchanged) |
| C | 0 | **44** |
| D | 0 | 0 |

**What was wrong.** The first pass classified a card as A whenever *at
least one* candidate had a usable implementation
(`any(ci["usable"] for ci in candidates)`). That is a materially weaker test
than the definition above, which requires *every* historically plausible
candidate to be implementable. Recomputing with the correct `all()` test
already flips all 44 to C, since every one of them has exactly one
implemented candidate and one that is not (below). A second, deeper question
had to be resolved first, though: whether `selection_at()`'s computed
candidate set is even the *right* set of historically-plausible outcomes to
run that test against - see "Selection-model ordering question".

**Worked example (Giant Rat, `erratum-giant-rat`), corrected.** This
document's first revision described Giant Rat's candidate 1 backwards, which
leaked into the proposed remediation for the whole 38-card cluster. Corrected
here, keeping the two readings explicitly separate as instructed.

Giant Rat's two relevant changes, in `changes[]` order:

- `changes[0]`: the Deck-verification/reveal-on-whiff ruling - DATED
  (`old_attested_through: 2011-02-02`) - confirmed **OLD** at the Edison
  snapshot (2010-04-24 predates 2011-02-02).
- `changes[1]`: the activation-semantics (no-valid-target-required) ruling -
  completely undated - **AMBIGUOUS**.

*(A) What the current linear model's version index actually means.*
`implementation_for_version(k)` is defined as "the implementation of the
version created by `changes[k-1]`". So version 0 = neither change has
happened; version 1 = `changes[0].resulting_implementation` = the version
created once `changes[0]` (the **verification** change) alone has happened,
i.e. **verification=NEW, activation=OLD**; version 2 (modern) = both have
happened. `implementation_for_version(1)` is `None` for Giant Rat.

*(B) The actual joint state historical evidence allows.* Verification is
confirmed OLD at Edison, not ambiguous. Activation semantics is completely
unknown. The two historically-plausible joint states are therefore
**verification=OLD, activation=OLD** (the baseline/GOAT-era combination) and
**verification=OLD, activation=NEW** (only activation-semantics has
modernised). Verification=NEW is not live at this snapshot at all - it is
ruled out by the record's own dating.

**(A) and (B) do not match.** Candidate 1, in the linear model's own defined
sense, means verification=NEW - a state the record's own dating already
rules out at Edison, not merely an "unimplemented" one. It is not the same
proposition as the real open question, verification=OLD/activation=NEW - and
that real question has **no valid version index at all** in Giant Rat's
`changes[]` ordering; it cannot be looked up via `implementation_for_version`,
correctly or otherwise. C is justified directly from the record's own prose,
not from candidate 1's slot happening to be empty: Giant Rat's `review.notes`
states plainly that "upstream ships one GOAT script encoding both ruling
behaviours ... so no implementation exists for a state in which only one had
changed" - that is the actual evidentiary basis, independent of what version
index the linear model happens to assign it.

**This mislabelling is not universal across the 38-card cluster - `changes[]`
list order flips it.** Giant Rat's dated-then-undated order is shared by
**29 of the 38** cluster records, all with the same broken correspondence
(candidate 1 requires an already-ruled-out state; the real intermediate state
has no index at all): Dedication through Light and Darkness, Elegant
Egotist, Emblem of Dragon Destroyer, Freed the Matchless General, Fusion
Sage, Giant Rat, Great Dezard, Hand of Nephthys, Hero Signal, Horus the
Black Flame Dragon LV4, Manju of the Ten Thousand Hands, Masked Dragon,
Mother Grizzly, Mystic Swordsman LV2, Mystic Swordsman LV4, Mystic Tomato,
Ninjitsu Art of Transformation, Pandemonium, Peten the Dark Clown, Pyramid
Turtle, Skull Knight #2, Sonic Bird, Terraforming, Thunder Dragon, Toon
Table of Contents, UFO Turtle, Ultimate Insect LV1, Ultimate Insect LV3,
Ultimate Insect LV5. The remaining **8 list the changes in the opposite
order** - undated activation-semantics first, dated verification second:
A Deal with Dark Ruler, Apprentice Magician, Armed Dragon LV3, Armed Dragon
LV5, Birdface, Bubonic Vermin, Dark Mimic LV1, Dark Scorpion - Meanae the
Thorn. For these 8, `implementation_for_version(1)` (= `changes[0]`'s slot,
and `changes[0]` here *is* the undated activation change) correctly and
coherently represents "activation alone has changed, verification remains
old" - the real intermediate state - and it is confirmed `None`, a genuine
gap rather than a coincidence involving an impossible slot. One further
cluster-1 record, Paladin of White Dragon, has three relevant changes (the
same undated activation/dated verification pair plus an unrelated,
already-resolved dated-2013 attack-restriction erratum its own review note
treats as a separate axis); its candidate 1 is likewise valid, for the same
list-order reason.

So within the 38-card cluster: **29 records have a self-contradictory linear
candidate set** with the true intermediate state unrepresented by any index;
**9 (8 plus Paladin) have a linear candidate set that happens to be valid**,
purely because of `changes[]` list order. In both groups the underlying
real-world fact is identical - two independent, unsequenceable ruling axes,
one pinned old by dating, one unknown - and every one of the 38 records' own
review notes says so in its own words. Only the mechanical validity of
`selection_at()`'s candidate *labels* differs, as an artifact of list order
the data model does not currently constrain.

**Independent-axis C vs. ordinary-linear-chain C: the required split.** Not
every C record has this independent-axis problem, and the two kinds must not
be conflated:

- **Independent-axis C: 38** - the entire failed-search/deck-verification
  cluster (all 38, spanning both the 29-broken and 9-valid groups above).
  Every one of these records' two relevant changes are two aspects of the
  *same* bundled ruling - upstream's single GOAT script encodes both the
  reveal-on-whiff procedure and the no-valid-target activation allowance
  together - and every one of their own review notes states outright that
  the two cannot be sequenced against each other.
- **Ordinary-linear-chain C: 6** - Axe of Despair, Tyrant Dragon, Vampire
  Lord, XY-Dragon Cannon, XYZ-Dragon Cannon, XZ-Tank Cannon. Each pairs one
  undated ruling with a *separate*, much later, mechanically-unrelated dated
  functional/text erratum (e.g. Axe of Despair: an undated
  `EFFECT_FLAG_DELAY` miss-timing ruling and an unrelated 2013 "always
  treated as an Archfiend card" text addition; Tyrant Dragon: an undated
  second-attack-condition ruling and an unrelated 2013 Graveyard-revival
  Tribute-timing erratum). These are two distinct historical events in the
  card's life, not two aspects of one bundled mechanic, and only one
  happens to be undated. All six have the `[AMBIGUOUS, OLD]` shape (undated
  ruling first, dated-and-necessarily-still-future erratum last), which is
  *always* internally valid under the linear model regardless of substance,
  because the dated change's already-confirmed-OLD status at Edison is
  consistent with the undated change having happened at any point before it
  - candidate 0 and candidate 1 are both ordinary, coherent chain positions.
  C is earned here the ordinary way: the undated ruling's chronology is
  unresolved, and the version it would create (candidate 1) has no recorded
  implementation. **Audited individually, not assumed**: this document's
  first revision incorrectly described all 6 as sharing Giant Rat's
  independent-axis structure; only Axe of Despair was flagged as an
  exception, when in fact all 6 are.

Total: 38 + 6 = **44**.

**B (41) and D (0) are unaffected.** The 41 divergence records were
re-checked for the same defect and do not have it: every one with more than
one relevant change (Blackwing - Sirocco the Dawn, Dark Necrofear,
Necrovalley [4 changes], Night Assailant, Soul Rope) has every change in its
chain carrying a real, specific `effective.date` - genuine, validated,
properly-ordered chronologies, not undated pairs. Their B classification and
the 41 count stand unchanged. No card required a D classification after
review - none of the 85 turned out to be a card-identity, region-scoping,
banlist, or engine-flag problem masquerading as an errata gap.

## Selection-model ordering question

The task raised a second, independent concern: does
`Erratum.selection_at()` (`retroformats/model.py:304-342`) correctly honour
`changes[]`'s documented contract - "Ordered oldest-to-newest"
(`schemas/erratum.schema.json:140`) - when computing candidates for a record
like Giant Rat?

**The mechanism.** `selection_at()` computes each relevant change's state
(OLD/AMBIGUOUS/NEW) at the snapshot, then derives a candidate range from two
*aggregate counts* - `definite_new` (how many changes are confirmed NEW) and
`definite_old` (how many are confirmed OLD) - not from each change's
position. For Giant Rat's `[OLD, AMBIGUOUS]` state vector this gives
`candidates=(0, 1)`.

**Is that consistent with a true chronological chain?** No, provably not.
If `changes[]` really is ordered oldest-to-newest, an earlier change
confirmed OLD (has not happened) logically forces every later change to also
be OLD (a later change cannot happen before an earlier one the chain says
hasn't happened yet) - so `[OLD, AMBIGUOUS]` should collapse to a
determinate version 0, not stay ambiguous with candidate 1 on the table.
Candidate 1 requires change 0 to be NEW, directly contradicting change 0's
own definite OLD state at this snapshot. By the mirror argument, `[AMBIGUOUS,
NEW]` should collapse to a determinate modern result, not stay ambiguous
with an unpropagated lower candidate. (The other two orderings the task
listed, `[NEW, AMBIGUOUS]` and `[AMBIGUOUS, OLD]`, are *not* affected by this
gap - an earlier change already having happened, or a later one not yet
having happened, does not constrain its neighbour on the other side either
way. All four cases, plus a multi-change widening case, are pinned by
`tests/test_errata.py::OrderingConstraintTest`.)

So there is a genuine, demonstrable gap between `selection_at()`'s candidate
computation and what a strict chronological chain would imply. The question
the task asked is which of two conclusions follows from that gap:

- **(A) `changes[]` is intended as a strict chronological chain**, in which
  case this is an algorithm bug: `selection_at()` should propagate definite
  states across neighbouring changes, and every affected format
  selection/warning count should be recomputed under the fix.
- **(B) these particular changes are independent behavioural axes** whose
  relative order is not established, in which case the linear version-chain
  representation cannot faithfully express them, "fixing" the algorithm to
  propagate would manufacture a false, overconfident answer, and the
  deficiency is in the data model, not the code.

**Finding: (B), for the 38-card independent-axis cluster specifically - not
for all 44.** This document's first revision over-generalised this finding
to all 44 known-wrong records, flagging only Axe of Despair as an exception.
That was wrong: the "A/B/C/D partition" section above establishes, per
record rather than by assumption, that only the **38 failed-search/
deck-verification cluster cards** are genuinely independent-axis records -
every one of their own review notes states, independently worded, that its
two changes cannot be sequenced against each other because they are two
aspects of one bundled GOAT script (Giant Rat's is quoted there in full).
The other **6 known-wrong records** (Axe of Despair, Tyrant Dragon, Vampire
Lord, XY-/XYZ-/XZ- Dragon/Tank Cannon) are ordinary, if partially-dated,
linear chains - two mechanically-unrelated historical events, not two
aspects of one ruling - and are unaffected by the (A)/(B) question below;
see "Independent-axis C vs. ordinary-linear-chain C" above for the full
per-record accounting.

For the 38, this reconciles cleanly with the repository's own validator,
which already does *not* enforce a fully-known total order:
`Validator._validate_errata`'s ordering check
(`retroformats/validate.py:285-309`) only rejects a *definite* inversion (a
later change's latest possible date earlier than an earlier change's
earliest possible date) and explicitly comments that "overlapping
uncertainty intervals are legitimate." A change with no bounds at all (like
the undated axis in all 38) can never trigger that check against anything,
in either direction - the validator was already written to tolerate not
knowing the exact order. What it was not written to tolerate - and what
this document is flagging - is a pair with essentially *no* shared timeline
information at all being fed through the same linear "how many of these N
changes have happened" arithmetic that works correctly for a partially-dated
but genuinely single-axis chain (which is exactly what the other 6 records
are, and exactly why they are not part of this finding).

**Why not just patch `selection_at()` for these 38 anyway?** Because
propagation would be *correct* for a genuine chain (like the other 6 C
records, or any of the 41 B records) and *wrong* for independent axes, and
nothing in `changes[]` currently distinguishes the two cases - the code has
no signal to decide, on a given pair, whether propagating is safe. Patching
it globally would silently convert Giant Rat's genuinely-two-dimensional
uncertainty (which of 2 joint states applies) into a false one-dimensional
certainty (a single "historical" answer), exactly the outcome the task
warned against ("do not force a false sequence"). This document proposes a
fix to the data model instead of the algorithm, scoped to the 38 records
that actually need it.

**Proposed smallest correct representation.** Add an optional per-change
field, e.g. `"order": "chained" | "independent"`, defaulting to `"chained"`
(preserving current semantics for every existing multi-change record,
including all 6 ordinary-chain C records and all 41 B records, which are
genuine dated or partially-dated chains). A change marked `"independent"`
declares that its relative order to the preceding change(s) is not
established - it is a separate behavioural axis, not a later position in the
same timeline. Then:

- for a run of `"chained"` changes, `selection_at()` performs the
  propagation described above (a strict improvement, safe because chained
  data is asserted to be genuinely ordered);
- for a run of `"independent"` changes, `selection_at()` computes the joint
  cross-product of per-axis OLD/AMBIGUOUS/NEW states rather than a single
  linear prefix index, and looks up implementation coverage per joint state
  rather than per position, instead of overloading a prefix-chain slot whose
  formal meaning may or may not line up with the real state depending on
  `changes[]` list order (see the 29-vs-9 split above - this is precisely
  the representational hazard a joint-state model removes). For the
  2-independent-axis case that covers 100% of the 38 affected records, the
  smallest viable storage change is for the independent change to carry its
  own `resulting_implementation_alone` field (the implementation for "only
  this axis has changed"), which for all 38 would be recorded as absent -
  turning today's prose-only "no implementation exists for the state between
  them" into a structured fact `selection_at()` and `validate.py` can check
  directly and consistently, regardless of list order.

No format selection or warning count changes as a result of this section -
this is a proposal, not an implementation, per the task's explicit scope.

## Qualitative-field audit

The task flagged one confirmed synthesis error (Tri-Blaze Accelerator, a
direction inversion between the LLM-generated blocker text and its own
canonical erratum record) and asked that every one of the 85 rows' three
generated fields (behavioural difference, blocker, recommended action) be
checked against its canonical `data/errata/*.json` record, not trusted
because the original 13-agent pass agreed with itself. All 85 were checked,
independently, against their source record - not sampled. **9 of 85 (10.6%)
had a genuine error**, spanning three distinct failure shapes:

- **Directional inversions** (old vs. new swapped, an earlier agent
  describing the era behaviour as the modern one or vice versa): Tri-Blaze
  Accelerator (implementation blocker), Masked Beast Des Gardius
  (implementation blocker and recommended action both told the custom
  script to implement the *modern* semi-nomi restriction instead of the
  era's strict nomi).
- **Unsupported/overstated claims**: Ninjitsu Art of Transformation,
  Paladin of White Dragon, and Pandemonium each claimed the shared
  `2011-02-02..2019-04-03` bracket covered *both* of their two relevant
  changes, when in every case only one change actually carries that bracket
  and the other is completely undated (a stronger, unsupported chronology
  claim); Elemental HERO Divine Neos cited a specific pre-errata print code
  not present anywhere in its canonical record.
- **Internal self-contradiction / factual mismatch against the record**:
  Soul Rope's recommended action silently dropped one of two required
  script conditions that its own blocker field (correctly) kept; Totem
  Dragon's recommended action asserted a resolution-time check the record
  explicitly says does not exist; Dark Master - Zorc's behavioural
  difference misattributed the Edison-era print version (the underlying
  behavioural claim was still correct - only the printing citation was
  wrong).

All corrections have been applied to the affected table rows below. Two of
the nine (Dark Master - Zorc, Elemental HERO Divine Neos) were errors only
in the `behavioural_difference` field, which is not rendered in any table in
this document - noted here for completeness, no table edit was needed for
either. The remaining 76 rows were checked and found to already correctly
and specifically reflect their canonical record.

## Root-cause clusters

Grouped by shared behavioural pattern, largest first. Every cluster below
accounts for all 85 cards exactly once (verified: 38+12+9+8+4+4+4+3+2+1 = 85).
"Leverage" states plainly what happens to the cluster's card count if the
ONE shared question that blocks it were resolved.


### 1. Failed-search / deck-verification behaviour — 38 cards, all partition C

**By far the largest cluster, and still the highest-leverage item in the
entire inventory - but not a chronology-only cluster, and an independent-axis
cluster whose candidate labelling is not uniform across all 38 (see below).**
Every one of the 38 cards' erratum records pairs the *same two ruling axes*:

- An **entirely undated** activation-semantics axis: the goat/historical
  script variant lets the effect be activated even when no legitimate
  target/match exists (in Deck, hand, or GY, depending on the card) — modern
  requires a valid match to exist before allowing activation at all.
- A verification/reveal-on-whiff axis, dated by the **same bracket on every
  single one of these 38 cards** — `old_attested_through: 2011-02-02`,
  `new_attested_from: 2019-04-03` — describing the accompanying procedure: on
  a proven failed search, the goat/historical script reveals and shuffles
  the relevant zone(s) (`Duel.GoatConfirm`) to prove the whiff to the
  opponent; the modern script does neither (it simply can't activate, so
  there's nothing to prove).

At the Edison snapshot (2010-04-24), the verification axis already resolves
determinately - **OLD** (2010-04-24 predates 2011-02-02, so the old
Deck-verification procedure was confirmed still in force) - and this alone
already rules out "modern" (which needs both axes to have changed). It is
the activation-semantics axis's *total absence of any date* that is the
actual source of the ambiguity: whether it had *also* already changed by
April 2010 is genuinely unknown, and there is no implementation anywhere
upstream for that combination (verification still old, activation already
modern) - only for "both still old" (the existing `reuse-upstream`
implementation, listed below) and "both modern" (the shipped card).
**Narrowing the verification axis's own 2011-02-02..2019-04-03 bracket
further (roadmap item 1b) would not change this cluster's classification at
all** - Edison already sits determinately in the old era for that axis, as
roadmap 1b's own text already notes. The actual open question for these 38
cards is the completely *undated* activation-semantics axis, which falls
under roadmap item 1a ("chronology for the undated era rulings"), not 1b.
`changes[]` lists these two axes in *different orders* across the 38 records
- 29 list the dated verification axis first (Giant Rat's order, under which
`selection_at()`'s own candidate 1 formally represents a state the dating
already rules out, and the true "verification-old/activation-new" state has
no valid index at all) and 8 plus Paladin of White Dragon list the undated
activation axis first (under which candidate 1 correctly represents that
state) - see "A/B/C/D partition" above for the exact split and why it does
not change the conclusion: every one of the 38 is **C**, argued from each
record's own review notes rather than from the version index, because the
activation axis's chronology is unresolved and the "verification-old,
activation-new" joint state - however it is (or isn't) labelled by
`selection_at()` - has no implementation.

**Leverage is still real, just two-branched instead of one, and directional
in a way the first pass got backwards.** Because all 38 cards share the
identical pair of ruling axes, a period source resolving the shared
activation-semantics question - *if* it turns out to govern this whole class
of "search and reveal-on-failure" effects rather than being decided
card-by-card (plausible, since all 38 share the same upstream script pattern
and the same verification-axis dating, but not yet confirmed as one single
historical policy announcement) - would have high leverage regardless of
which way it resolves:

- If it confirms activation-semantics had **not** yet modernised by
  2010-04-24 (both axes still old), the existing `reuse-upstream`
  implementation is simply correct and this cluster needs zero further work,
  exactly as the first pass concluded.
- If it confirms activation-semantics **had** already modernised by
  2010-04-24 while verification/reveal-on-whiff remained old, the needed
  custom script must **add** the modern-style valid-target-exists check at
  activation (which the existing GOAT/baseline script lacks entirely, not
  remove one - the baseline encodes the *old* activation semantics, which
  has no such check), while *also* retaining the old-era reveal-on-whiff
  procedure for the narrower case where an activation-legal target
  subsequently becomes unavailable before resolution (a valid target existing
  at activation does not guarantee one still exists at resolution, once
  other chain links have resolved first - "requires a valid match to
  activate" and "verify on a resolution-time whiff" are separate, not
  mutually exclusive, behaviours). This is the reverse of what this
  document's first revision described.

Either answer is actionable for all 38 cards at once, once confirmed; only
the research step (not the possible follow-up script) would be in scope for
a future milestone - see "Recommended next milestone" below for why even the
research step is not started in this commit.


| Card | Passcode | Erratum ID | Missing valid-target check on | Baseline (both axes old) implementation — no implementation exists for verification-old/activation-new (all partition C) | Recommended action |
|---|---|---|---|---|---|
| A Deal with Dark Ruler | 6850209 | `erratum-a-deal-with-dark-ruler` | Berserk Dragon | `504700010` | locate a dated period ruling (2010-2019) on when A Deal with Dark Ruler's activation began requiring a valid… |
| Apprentice Magician | 9156135 | `erratum-apprentice-magician` | (see erratum record) | `504700013` | locate a dated period ruling on when Apprentice Magician's revival effect required a Level 2 or lower… |
| Armed Dragon LV3 | 980973 | `erratum-armed-dragon-lv3` | Armed Dragon LV5 | `504700003` | locate a dated period ruling on when Armed Dragon LV3's Standby Phase activation began requiring a valid… |
| Armed Dragon LV5 | 46384672 | `erratum-armed-dragon-lv5` | Armed Dragon LV7 | `504700075` | locate a dated period ruling on when Armed Dragon LV5's End Phase activation began requiring a valid 'Armed… |
| Birdface | 45547649 | `erratum-birdface` | Harpie Lady | `504700073` | locate a dated period ruling on when Birdface's battle-destruction trigger began requiring a valid 'Harpie… |
| Bubonic Vermin | 6104968 | `erratum-bubonic-vermin` | Bubonic Vermin | `504700008` | locate a dated period ruling on when Bubonic Vermin's FLIP effect began requiring a second copy to exist in… |
| Dark Mimic LV1 | 74713516 | `erratum-dark-mimic-lv1` | Dark Mimic LV3 | `504700129` | locate a dated period ruling or rulebook fixing when the no-eligible-target activation allowance for Dark… |
| Dark Scorpion - Meanae the Thorn | 74153887 | `erratum-dark-scorpion-meanae-the-thorn` | Dark Scorpion | `504700125` | locate a dated period ruling fixing when the no-eligible-'Dark Scorpion'-card activation allowance for… |
| Dedication through Light and Darkness | 69542930 | `erratum-dedication-through-light-and-darkness` | Dark Magician of Chaos | `504700113` | locate a dated period ruling fixing when the no-eligible-'Dark Magician of Chaos' activation allowance for… |
| Elegant Egotist | 90219263 | `erratum-elegant-egotist` | Harpie Lady | `504700157` | locate a dated period ruling fixing when the no-eligible-Harpie activation allowance for Elegant Egotist ended |
| Emblem of Dragon Destroyer | 6390406 | `erratum-emblem-of-dragon-destroyer` | Buster Blader | `504700009` | locate a dated period ruling fixing when the no-eligible-'Buster Blader' activation allowance for Emblem of… |
| Freed the Matchless General | 49681811 | `erratum-freed-the-matchless-general` | (see erratum record) | `504700082` | locate a dated period ruling fixing when the no-eligible-Warrior activation allowance for Freed the… |
| Fusion Sage | 26902560 | `erratum-fusion-sage` | Polymerization | `504700047` | locate a dated period ruling fixing when the no-eligible-'Polymerization' activation allowance for Fusion… |
| Giant Rat | 97017120 | `erratum-giant-rat` | (see erratum record) | `504700172` | locate a dated period ruling on when Giant Rat lost its no-target-required activation allowance for the… |
| Great Dezard | 88989706 | `erratum-great-dezard` | Fushioh Richie | `504700154` | locate a dated period ruling on when Great Dezard lost its no-target-required activation allowance for its… |
| Hand of Nephthys | 98446407 | `erratum-hand-of-nephthys` | Sacred Phoenix of Nephthys | `504700175` | locate a dated period ruling on when Hand of Nephthys lost its no-target-required activation allowance for… |
| Hero Signal | 22020907 | `erratum-hero-signal` | Elemental HERO | `504700031` | locate a dated period ruling on when Hero Signal lost its no-target-required activation allowance for its… |
| Horus the Black Flame Dragon LV4 | 75830094 | `erratum-horus-the-black-flame-dragon-lv4` | Horus the Black Flame Dragon LV6 | `504700132` | locate a dated period ruling on when Horus the Black Flame Dragon LV4 lost its no-target-required activation… |
| Manju of the Ten Thousand Hands | 95492061 | `erratum-manju-of-the-ten-thousand-hands` | (see erratum record) | `504700169` | locate a dated period ruling on when Manju of the Ten Thousand Hands lost its no-target-required activation… |
| Masked Dragon | 39191307 | `erratum-masked-dragon` | (see erratum record) | `504700064` | locate a dated period ruling on when Masked Dragon lost its no-target-required activation allowance for its… |
| Mother Grizzly | 57839750 | `erratum-mother-grizzly` | (see erratum record) | `504700093` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-reveal proof requirement ended; separately, no source at all dates when the activate-without-a-Deck-target allowance was tightened |
| Mystic Swordsman LV2 | 47507260 | `erratum-mystic-swordsman-lv2` | (see erratum record) | `504700077` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the hand+Deck reveal requirement ended; separately, no source at all dates when the activate-without-an-LV4-target allowance was tightened |
| Mystic Swordsman LV4 | 74591968 | `erratum-mystic-swordsman-lv4` | (see erratum record) | `504700128` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the hand+Deck reveal requirement ended; separately, no source at all dates when the activate-without-an-LV6-target allowance was tightened |
| Mystic Tomato | 83011277 | `erratum-mystic-tomato` | (see erratum record) | `504700142` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-reveal proof requirement ended; separately, no source at all dates when the activate-without-a-Deck-target allowance was tightened |
| Ninjitsu Art of Transformation | 70861343 | `erratum-ninjitsu-art-of-transformation` | (see erratum record) | `504700115` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the hand+Deck reveal requirement ended; separately, no source at all in the packet dates when the activate-without-a-target allowance for the Ninja-Tribute cost was tightened |
| Paladin of White Dragon | 73398797 | `erratum-paladin-of-white-dragon` | (see erratum record) | `504700119` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the hand+Deck reveal requirement ended; separately, no source at all dates when the self-Tribute activate-without-a-Blue-Eyes-target allowance was tightened |
| Pandemonium | 94585852 | `erratum-pandemonium` | (see erratum record) | `504700165` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-reveal proof requirement ended; separately, no source at all dates when the activate-without-a-Deck-target allowance was tightened |
| Peten the Dark Clown | 52624755 | `erratum-peten-the-dark-clown` | (see erratum record) | `504700084` | locate a dated period ruling or tournament-policy note pinning when Deck/Hand verification for Peten's… |
| Pyramid Turtle | 77044671 | `erratum-pyramid-turtle` | (see erratum record) | `504700135` | locate a dated period ruling pinning when Deck verification for Pyramid Turtle's Special Summon trigger… |
| Skull Knight #2 | 15653824 | `erratum-skull-knight-2` | Skull Knight #2 | `504700022` | locate a dated period ruling pinning when Deck verification for Skull Knight #2's search ended (between… |
| Sonic Bird | 57617178 | `erratum-sonic-bird` | (see erratum record) | `504700092` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-verification requirement ended; separately, no source at all dates when the fail-to-find (no-target) activation allowance was tightened |
| Terraforming | 73628505 | `erratum-terraforming` | (see erratum record) | `504700121` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-verification requirement ended; separately, no source at all dates when the fail-to-find (no-target) activation allowance was tightened |
| Thunder Dragon | 31786629 | `erratum-thunder-dragon` | Thunder Dragon | `504700054` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-verification requirement ended; separately, no source at all dates when the zero-copy/no-target discard-activation allowance was tightened |
| Toon Table of Contents | 89997728 | `erratum-toon-table-of-contents` | Toon | `504700156` | locate a dated period ruling narrowing the 2011-02-02..2019-04-03 window for when the Deck-verification requirement ended; separately, no source at all dates when the fail-to-find (no-target) activation allowance was tightened |
| UFO Turtle | 60806437 | `erratum-ufo-turtle` | (see erratum record) | `504700098` | locate a dated period ruling establishing when UFO Turtle's trigger began requiring a valid… |
| Ultimate Insect LV1 | 49441499 | `erratum-ultimate-insect-lv1` | Ultimate Insect LV3 | `504700081` | locate a dated period ruling establishing when Ultimate Insect LV1's cost began requiring a… |
| Ultimate Insect LV3 | 34088136 | `erratum-ultimate-insect-lv3` | Ultimate Insect LV5 | `504700057` | locate a dated period ruling establishing when Ultimate Insect LV3's cost began requiring a… |
| Ultimate Insect LV5 | 34830502 | `erratum-ultimate-insect-lv5` | Ultimate Insect LV7 | `504700058` | locate a dated period ruling establishing when Ultimate Insect LV5's cost began requiring a… |


### 2. Other shared ruling-era changes — 12 cards, all partition B

Chronology is already resolved for all 12; each needs a **custom Lua script
that does not yet exist upstream**. Not one undifferentiated bucket — two
sub-patterns recur within it, independently identified by the diagnostic
pass from each card's own erratum text:

- **Nomi-to-semi-nomi wording revision** (~7 of 12: Elemental HERO Chaos
  Neos, Garuda the Wind Spirit, Gigantes, Gladiator Beast Heraklinos,
  Malefic Blue-Eyes White Dragon, Metalzoa, VW-Tiger Catapult): a TCG-wide
  errata wave converted strict "can only be Special Summoned by X" wording to
  "Must first be Special Summoned... by X," loosening a permanent lock into a
  one-time-procedure lock. Edison predates this wave; the Edison-era text is
  the strict version.
- **Union Condition removal** (2 of 12: Machina Gearframe, Machina
  Peacekeeper): the "a monster can only be equipped with 1 Union monster at a
  time" clause, printed on every period Union monster, was later dropped from
  reprints.
- Genuinely distinct: Dark Necrofear, Evil HERO Dark Gaia, Necrovalley (3).

**Leverage:** none of these need chronology research (already resolved) —
the leverage here is **implementation reuse**: a shared "strict Nomi lock"
Lua helper pattern could be written once and applied to the ~7
nomi-to-semi-nomi cards, and a shared "Union equip-restriction" helper to the
2 Union cards, cutting per-card script-writing effort even though each still
needs its own passcode, CDB row, and script file.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Dark Necrofear | 31829185 | `erratum-dark-necrofear` | **B** | none | no upstream implementation matches v4's text (the only candidate, the manga-only unofficial passcode 511004006, has a different summon… | write a custom Lua script restoring the strict Nomi lock and an untargeted End Phase equip/control-theft… |
| Elemental HERO Chaos Neos | 17032740 | `erratum-elemental-hero-chaos-neos` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs an EFFECT_SPSUMMON_CONDITION… | write a custom Lua script restoring the strict Fusion-only Nomi lock and an either-Main-Phase coin toss +… |
| Evil HERO Dark Gaia | 58332301 | `erratum-evil-hero-dark-gaia` | **B** | none | no upstream implementation exists at all (this card has no historical or unofficial variant of any kind); the historical script needs to… | write a custom Lua script that captures field ATK at the moment of Fusion Summon and makes the… |
| Garuda the Wind Spirit | 12800777 | `erratum-garuda-the-wind-spirit` | **B** | none | no upstream implementation exists at all (this card has no historical or unofficial variant of any kind); the historical script needs an… | write a custom Lua script restoring the strict Nomi lock (no revival after proper summon) + reserve a passcode |
| Gigantes | 47606319 | `erratum-gigantes` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must impose a permanent nomi… | write a custom Lua script enforcing a permanent (post-Summon-persistent) strict-nomi restriction disallowing… |
| Gladiator Beast Heraklinos | 27346636 | `erratum-gladiator-beast-heraklinos` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must impose a permanent nomi… | write a custom Lua script enforcing a permanent strict-nomi restriction on Special Summons after Heraklinos… |
| Machina Gearframe | 42940404 | `erratum-machina-gearframe` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must add a check refusing to… | write a custom Lua script enforcing the one-Union-monster-per-host equip restriction and forcing face-up… |
| Machina Peacekeeper | 78349103 | `erratum-machina-peacekeeper` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must add a check refusing to… | write a custom Lua script enforcing the one-Union-monster-per-host equip restriction and forcing face-up… |
| Malefic Blue-Eyes White Dragon | 9433350 | `erratum-malefic-blue-eyes-white-dragon` | **B** | none | No usable implementation exists: the only upstream match, passcode 513000068, is a different anime-only card with a different cost (sends… | write a custom Lua script enforcing the strict Deck-banish nomi (no later generic revival) and the… |
| Metalzoa | 50705071 | `erratum-metalzoa` | **B** | none | No upstream implementation exists for 50705071. A custom script must enforce the strict Deck-only nomi (Special Summon only via the… | write a custom Lua script enforcing the strict Deck-only nomi with no post-Summon revival, and reserve a… |
| Necrovalley | 47355498 | `erratum-necrovalley` | **B** | none | The only upstream historical Necrovalley (511002998) implements the later movement-scoped 2012 text with a re:GetHandler() self-move… | write a custom Lua script negating only effects that target a card in either Graveyard (the TU02-EN014 scope… |
| VW-Tiger Catapult | 58859575 | `erratum-vw-tiger-catapult` | **B** | none | Modern/upstream script's Special Summon procedure check must revert from the semi-Nomi 'restricts only the first Special Summon' condition… | write a custom Lua script for VW-Tiger Catapult enforcing a full Nomi restriction (Special Summonable only… |


### 3. Once-per-turn / name-lock changes — 9 cards, all partition B

Chronology already resolved for all 9; each needs a custom script that
removes an OPT (once-per-turn) guard, or a by-name lock, the modern script
carries but the period text/lineage does not. D.D. Scout Plane and D.D.
Survivor share an identical "End Phase return, no OPT guard" pattern; Dark
Master - Zorc, Dice Re-Roll, Goddess of Whim, and Second Coin Toss share an
"unrestricted die/coin redo effect" pattern; Totem Dragon and Treeborn Frog
share a "Standby Phase self-revival, no OPT" pattern; Strike Ninja is a
by-name-vs-per-copy lock distinction. **Leverage:** implementation-pattern
reuse across the sub-groups noted, not a single shared script.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| D.D. Scout Plane | 3773196 | `erratum-d-d-scout-plane` | **B** | none | The modern script gates the End Phase return with a once-per-turn guard that the SDDE/DR2-era text does not carry; a custom script must… | write a custom Lua script removing the once-per-turn guard on the End Phase return trigger + reserve a… |
| D.D. Survivor | 48092532 | `erratum-d-d-survivor` | **B** | none | The modern script gates the End Phase return with a once-per-turn guard that the pre-LCGX SDDE-era text does not carry; a custom script… | write a custom Lua script removing the once-per-turn guard on the End Phase return trigger + reserve a… |
| Dark Master - Zorc | 97642679 | `erratum-dark-master-zorc` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs to grant the die-roll effect with… | write a custom Lua script for the die-roll Ignition Effect with no once-per-turn cap (repeatable within a… |
| Dice Re-Roll | 83241722 | `erratum-dice-re-roll` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs to grant a per-copy (not per-turn)… | write a custom Lua script granting a per-copy, six-sided-die-only re-roll effect with no per-turn gain cap +… |
| Goddess of Whim | 67959180 | `erratum-goddess-of-whim` | **B** | none | no usable historical implementation exists upstream (upstream_implementations is empty); a custom script must reproduce the unrestricted… | write a custom Lua script removing the once-per-turn limiter on the coin-toss ATK-double/halve Ignition… |
| Second Coin Toss | 36562627 | `erratum-second-coin-toss` | **B** | none | No usable implementation exists (upstream_implementations empty); a custom script must grant a per-copy (not by-name) once-per-turn redo,… | write a custom Lua script granting a per-copy (not by-name) once-per-turn coin-toss redo, reserve a passcode |
| Strike Ninja | 41006930 | `erratum-strike-ninja` | **B** | none | No usable implementation exists: the only upstream code, 153000011 'Strike Ninja (Deck Master)', carries the modern by-name once-per-turn… | write a custom Lua script restoring the per-copy (not by-name) once-per-turn limit on the self-banish… |
| Totem Dragon | 564541 | `erratum-totem-dragon` | **B** | none | Modern/upstream script behaviour must drop the once-per-turn registration on the Standby Phase revival trigger so a negated activation can… | write a custom Lua script for Totem Dragon's Standby Phase self-revival without an OPT limiter, preserving the you-control-no-monsters check (enforced at both activation and resolution) and the all-Dragon-in-GY check (activation-only in both period and modern text, not re-checked at resolution)… |
| Treeborn Frog | 12538374 | `erratum-treeborn-frog` | **B** | none | Modern/upstream script's Standby Phase revival trigger must drop its once-per-turn registration so a negated activation can retrigger the… | write a custom Lua script for Treeborn Frog's Standby Phase self-revival without an OPT limiter, preserving… |


### 4. Target legality — 8 cards (7 partition B, 1 partition C)

What a targeted effect may legally target changed — mostly (7 of 8)
targeting-vs-non-targeting or scope-narrowing text errata with chronology
already resolved and no shared sub-pattern beyond the general category (each
needs its own bespoke script). One (XY-Dragon Cannon) is partition C, but
**not** an independent-axis case like cluster 1: it pairs an undated
contact-fusion-material ruling with a separate, much later (2016), mechanically
unrelated nomi-wording erratum - an ordinary partially-dated linear chain
(see "Independent-axis C vs. ordinary-linear-chain C" above), sharing the
Cannon-fusion contact-material question with the cost-payment cluster below.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Masked Beast Des Gardius | 48948935 | `erratum-masked-beast-des-gardius` | **B** | none | No upstream implementation exists at all for 48948935. A custom script must make the Mask of Remnants equip a non-targeting, on-resolution selection open to any monster on the field, and must implement the era's strict nomi (Tribute-only Special Summon, no source zone, no later generic revival) rather than the modern semi-nomi hand-bound… | write a custom Lua script implementing the non-targeting on-resolution equip-to-any-monster effect plus the era's strict nomi restriction (Special Summon only by Tributing 2 monsters incl. 1 named Tiki/Melchid, no source zone, no later generic revival)… |
| Night Assailant | 16226786 | `erratum-night-assailant` | **B** | none | Upstream's only historical variant (cards-unofficial 16226796) already implements a SelectTarget exception excluding e:GetHandler(), which… | write a custom Lua script removing the SelectTarget self-exclusion so Night Assailant can legally target and… |
| Red-Eyes Wyvern | 67300516 | `erratum-red-eyes-wyvern` | **B** | none | No upstream implementation exists for 67300516. A custom script must make the GY revival a non-targeting, on-resolution selection, restore… | write a custom Lua script implementing the non-targeting on-resolution revival with the Red-Eyes B. Chick… |
| Super Vehicroid - Stealth Union | 3897065 | `erratum-super-vehicroid-stealth-union` | **B** | none | No usable implementation exists: the only upstream code, 511002959 'Super Vehicroid - Stealth Union (Anime)', is a distinct card granting… | write a custom Lua script restricting the equip-target filter to 'monster you control, except Machine-Type',… |
| Swap Frog | 9126351 | `erratum-swap-frog` | **B** | none | No usable implementation exists (upstream_implementations empty); a custom script must drop the face-up requirement from the field-mill… | write a custom Lua script dropping the face-up-only mill restriction and restoring the 'Frog the Jam'… |
| Trap of Darkness | 79766336 | `erratum-trap-of-darkness` | **B** | none | Modern/upstream script's Normal-Trap-in-GY target filter must drop the 'except Trap of Darkness' self-exclusion so a second copy of the… | write a custom Lua script for Trap of Darkness with a Normal-Trap-in-GY target filter that does not exclude… |
| Wild Fire | 68815401 | `erratum-wild-fire` | **B** | none | Modern/upstream script's destroy-target filter must narrow from 'all Blaze Accelerator cards you control' back to 'a single face-up Blaze… | write a custom Lua script for Wild Fire that destroys one face-up 'Blaze Accelerator' card as its target and… |
| XY-Dragon Cannon | 2111707 | `erratum-xy-dragon-cannon` | **C** | `504700007` (candidate 0 only — no implementation for the intermediate candidate) | No source in the packet dates when (or whether) XY-Dragon Cannon's contact-fusion material eligibility was extended from Monster-Zone-only… | locate a dated period ruling on whether XY-Dragon Cannon's contact-fusion material could already include a… |


### 5. Cost/payment behaviour — 4 cards (2 partition C, 2 partition B)

XYZ-Dragon Cannon and XZ-Tank Cannon (partition C - ordinary linear chains,
like XY-Dragon Cannon, not independent-axis cases) share an unresolved
chronology question with XY-Dragon Cannon in the target-legality cluster
above: when TCG rulings on contact-fusion material eligibility for the
"Cannon" lineage changed - **a second, smaller shared-chronology
opportunity** (3 cards total across the two clusters, all C not A: the
baseline `reuse-upstream` implementation is confirmed, but none of the three
has any implementation for the candidate created once the undated
material-eligibility ruling alone has changed) alongside the headline
search-verification one. Blaze Accelerator and Tri-Blaze Accelerator
(partition B) share a "Pyro-Type send must be an unconditional activation
cost, not a conditional resolution step" pattern needing a custom script
each.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Blaze Accelerator | 69537999 | `erratum-blaze-accelerator` | **B** | none | The modern script locks a PSCT target at activation and defers the Pyro-Type send into the resolution as a conditional step; the FOTB-EN041/Edison-era text instead paid the send as an unconditional cost at activation, with no target locked until resolution. A custom… | write a custom Lua script moving the Pyro-Type-to-GY send back into an unconditional activation cost (and dropping the on-activation target lock) rather than… |
| Tri-Blaze Accelerator | 21420702 | `erratum-tri-blaze-accelerator` | **B** | none | The modern script defers the Pyro-Type send into the resolution as a conditional step (paid only if the destroy step executes); the FOTB-EN041/Edison-era text instead paid the send as an unconditional cost at activation, with the destruction and the burn resolving side by side. A custom… | write a custom Lua script for Tri-Blaze Accelerator that pays the Pyro-Type send as an activation cost and… |
| XYZ-Dragon Cannon | 91998119 | `erratum-xyz-dragon-cannon` | **C** | `504700161` (candidate 0 only — no implementation for the intermediate candidate) | An exact date or bounded interval for when the TCG ruling on contact-fusion material eligibility shifted from 'only monsters physically in… | locate a dated period ruling (Konami FAQ or Shonen Jump judge column) on whether Cannon-lineage… |
| XZ-Tank Cannon | 99724761 | `erratum-xz-tank-cannon` | **C** | `504700177` (candidate 0 only — no implementation for the intermediate candidate) | An exact date or bounded interval for when the TCG ruling on contact-fusion material eligibility shifted from 'only monsters physically in… | locate a dated period ruling (Konami FAQ or Shonen Jump judge column) on whether Cannon-lineage… |


### 6. Activation-condition changes — 4 cards (1 partition C, 3 partition B)

No shared sub-pattern beyond the general category; each is a distinct
activation-legality question (Main-Phase gating, attacker-condition scope, a
Nomi condition, and a second-attack restriction on Tyrant Dragon). Tyrant
Dragon is partition C, but - like the other 5 reclassified non-cluster-1
cards - an ordinary linear chain, not an independent-axis case: its undated
ruling (a second-attack condition) and its dated 2013 functional erratum (a
Graveyard-revival Tribute-timing change) are two mechanically unrelated
historical events, not two aspects of one bundled ruling.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Blackwing - Sirocco the Dawn | 75498415 | `erratum-blackwing-sirocco-the-dawn` | **B** | none | The modern script gates the Ignition effect to a Main Phase-1-only activation location and applies an End-Phase reset to the granted ATK;… | write a custom Lua script removing the Main Phase 1-only activation gate and the End Phase ATK-gain expiry +… |
| Blast Held by a Tribute | 89041555 | `erratum-blast-held-by-a-tribute` | **B** | none | The modern script's activation check tests only whether the attacking monster was Tribute Summoned; a custom Edison-era script must widen… | write a custom Lua script widening the activation trigger to also accept an attack by a Tribute-Set monster… |
| The Rock Spirit | 76305638 | `erratum-the-rock-spirit` | **B** | none | No usable implementation exists (upstream_implementations empty; Project Ignis ships neither a GOAT nor a pre-errata variant); a custom… | write a custom Lua script enforcing the strict Nomi-only Special Summon condition with no later revival by… |
| Tyrant Dragon | 94568601 | `erratum-tyrant-dragon` | **C** | `504700164` (candidate 0 only — no implementation for the intermediate candidate) | No dated period ruling establishes when (or whether) the 'first attack must have been against a monster, not direct' restriction on Tyrant… | locate a dated period ruling on whether Tyrant Dragon's second attack already required the first attack to… |


### 7. Genuinely card-specific errata — 4 cards, all partition B

No shared ruling-era pattern identified for any of these four - each is a
one-off text/functional erratum needing its own bespoke script (an archetype
membership addition, a disposal-branch condition change, a Fusion Material
filter, and a Summon-prevention effect scope change).


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| A Hero Emerges | 21597117 | `erratum-a-hero-emerges` | **B** | none | The modern script's 'Otherwise, send to GY' branch fires whenever the revealed monster cannot be Special Summoned; a custom Edison-era… | write a custom Lua script gating the disposal branch on 'not a Monster Card' rather than 'cannot be Special… |
| Elemental HERO Divine Neos | 31111109 | `erratum-elemental-hero-divine-neos` | **B** | none | no upstream implementation exists at all (upstream_implementations empty); the historical script needs a Fusion Material filter and cost… | write a custom Lua script with an explicit Neos-only (excluding Neo Space) material/cost filter + reserve a… |
| Ido the Supreme Magical Force | 35984222 | `erratum-ido-the-supreme-magical-force` | **B** | none | no usable historical implementation exists upstream (the packet's one upstream entry, passcode 511003208 'Ido The Supreme Magical Force… | write a custom Lua script omitting EFFECT_CANNOT_MSET from the Summon-prevention effect and reserve a… |
| Mustering of the Dark Scorpions | 68191243 | `erratum-mustering-of-the-dark-scorpions` | **B** | none | No upstream implementation exists for 68191243. A custom script must restrict Special Summon eligibility to English card-name string… | write a custom Lua script restricting eligible targets to name-match("Dark Scorpion") plus the named Cliff… |


### 8. Trigger registration — 3 cards (1 partition C, 2 partition B)

Distinct from the miss-timing/EFFECT_FLAG_DELAY cluster below: these are
about *which event* a trigger is registered against or *what it checks*
(controller/face-up-state filters, REASON_EFFECT exclusions), not about
whether the trigger exempts itself from missing the timing. Vampire Lord is
partition C, but - like the other 5 reclassified non-cluster-1 cards - an
ordinary linear chain, not an independent-axis case: its undated ruling
(self-revival zone scope) and its dated 2016 functional erratum (a
once-per-turn cap) are two mechanically unrelated historical events, not two
aspects of one bundled ruling.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Boss Rush | 66947414 | `erratum-boss-rush` | **B** | none | The modern script's trigger checks controller and face-up-this-turn flags on the destroyed 'B.E.S.' monster, adds a 'no Normal Summon this… | write a custom Lua script broadening the destruction trigger to either player's B.E.S./Big Core in any… |
| Soul Rope | 37383714 | `erratum-soul-rope` | **B** | none | No usable implementation exists: the only upstream code, 511001593 'Soul Rope (Anime)', is a distinct card matching no lineage version and… | write a custom Lua script using EVENT_DESTROYED with EFFECT_FLAG_DAMAGE_STEP and a cfilter carrying no REASON_EFFECT/REASON_DESTROY test (both absent, not just REASON_EFFECT), retaining the sent-to-GY requirement, and reserve a passcode |
| Vampire Lord | 53839837 | `erratum-vampire-lord` | **C** | `504700087` (candidate 0 only — no implementation for the intermediate candidate) | No source in the packet dates when (or whether) Vampire Lord's self-revival stopped being restricted to… | locate a dated period ruling on whether Vampire Lord's Standby Phase revival was already restricted to being… |


### 9. Damage Step activation windows — 2 cards, both partition B

Both need a custom script changing which event/condition a Damage-Step-
relevant trigger checks; no shared sub-pattern beyond the general category
given only two cards.


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Green Baboon, Defender of the Forest | 46668237 | `erratum-green-baboon-defender-of-the-forest` | **B** | none | no usable historical implementation exists upstream (the packet's one upstream entry, passcode 511001661 'Green Baboon, Defender of the… | write a custom Lua script switching the trigger to EVENT_DESTROYED with no face-up filter and adding… |
| Rise of the Snake Deity | 16067089 | `erratum-rise-of-the-snake-deity` | **B** | none | No usable implementation exists: the packet's only upstream code, 511002525 'Rise of the Sacred Deity (Anime)', is a different card and… | write a custom Lua script removing the battle-destruction exclusion and adding… |


### 10. Miss-timing / EFFECT_FLAG_DELAY — 1 card, partition C

Axe of Despair is an **ordinary linear chain**, not an independent-axis
case - the one this document's earlier revision used as the sole worked
example of the distinction, and, per the corrected accounting above, the
same shape (not a "different" one) as the other 5 reclassified
non-cluster-1 cards: its undated change is the *earlier* relevant one, the
dated one *later* - `[AMBIGUOUS, OLD]`, one of the two orderings that is
*not* affected by the propagation gap discussed above. Its undated ruling
(an `EFFECT_FLAG_DELAY` miss-timing exemption) and its dated 2013-06-28
functional erratum (an unrelated "always treated as an Archfiend card" text
addition) are two mechanically unrelated historical events in the card's
life, not two aspects of one bundled ruling - the defining property of an
ordinary-chain C record. `selection_at()` reports `candidates=(0, 1)` at the
Edison snapshot: candidate 0 (baseline) is implemented, and candidate 1 (the
undated `EFFECT_FLAG_DELAY` change in effect, the dated 2013 Archfiend
change not yet in effect) has no `resulting_implementation` - a valid,
non-contradictory chain position, unlike Giant Rat's candidate 1. That is C,
not A, for the ordinary reason: chronology of the undated ruling is
unresolved, and the version it would create has no recorded implementation.
Note also: the record's own `review.notes` asserts "only the baseline is
ever selected" because both project snapshots (2005-04-01, 2010-04-24)
precede the dated 2013 change - but that reasoning overlooks that the
*undated* ruling change contributes its own, independent ambiguity
regardless of the dated change's date, which is exactly what the live
selection computation above shows. This is flagged here as a secondary
finding from this audit, not corrected in the underlying data record (out
of scope for an audit-only milestone).


| Card | Passcode | Erratum ID | Partition | Existing implementation | Blocker (short) | Recommended action |
|---|---|---|---|---|---|---|
| Axe of Despair | 40619825 | `erratum-axe-of-despair` | **C** | `504700068` (candidate 0 only — no implementation for the intermediate candidate) | An exact date or bounded interval for when Axe of Despair's send-to-Graveyard trigger stopped being exempt from missing the timing (i.e.,… | locate a dated period ruling on when Axe of Despair's Graveyard-send trigger lost its exemption from missing… |

## Prioritisation

Two evidence-internal views, kept separate as instructed. No popularity,
"meta," or deck-prevalence claim appears anywhere below — this project has
not gathered sourced Edison-era tournament/deck data, and none is used here.

### Leverage priority (cards correctable per shared question/pattern)

| Rank | Cluster | Cards | What resolves it |
|---|---|---|---|
| 1 | Failed-search / deck-verification | **38** | *if* a period source is found that governs the shared, completely undated activation-semantics question for this whole class of effect (not yet confirmed as one single historical policy, but plausible given the identical script pattern across all 38 - see cluster 1 above) - resolves *either* to "existing implementation is correct, zero further work" *or* to "all 38 need the same one shared custom-script pattern," not a chronology-only cluster. This is roadmap item 1a territory (undated era rulings), not 1b (the companion verification-axis interval, already resolved old at Edison and not the open question here) |
| 2 | Cannon-lineage contact-fusion material (XY-/XYZ-/XZ- Dragon/Tank Cannon, split across target-legality + cost-payment above) | **3** | same shape and same 1a/not-1b caveat as row 1, for the separate undated contact-fusion-material-eligibility ruling shared by these three (an ordinary linear chain, not an independent-axis case - see "Independent-axis C vs. ordinary-linear-chain C" above) |
| 3 | Nomi-to-semi-nomi wording (within cluster 2) | **~7** | one reusable "strict Nomi lock" Lua pattern (chronology already resolved) |
| 4 | Union Condition removal (within cluster 2) | **2** | one reusable "Union equip restriction" Lua pattern (chronology already resolved) |
| 5 | Once-per-turn/name-lock sub-groups (D.D. pair; die/coin-redo quartet; Standby-revival pair) | **8** of 9 | up to 3 reusable OPT-removal patterns (chronology already resolved) |
| — | Everything else (target-legality remainder, activation-condition, card-specific, trigger-registration, damage-step, miss-timing) | **26** | no shared question or pattern found; bespoke per card |

Rows 1 and 2 are RESEARCH leverage (chronology questions whose answer also
determines whether a shared follow-up script is needed - see the corrected
A/B/C/D partition above); rows 3-5 are IMPLEMENTATION leverage (shared
script patterns, chronology already settled, no research needed at all).
Row 1 alone accounts for 38/85 = 44.7% of every card this milestone covers.

### Severity priority (nature of the behavioural deviation, not frequency)

Ranked by what the deviation actually does to a legal play, most severe
first:

1. **Functional lockout — a legal action is entirely unavailable.** The
   effect cannot be activated at all in modern where period evidence says an
   Edison-era player could attempt it (even a doomed attempt, revealed as a
   proven whiff, was itself a legal, informative action). Covers the
   **38-card** failed-search/deck-verification cluster in full, plus the
   Main-Phase-gated and attacker-condition cards in
   activation-condition-changes (**Blackwing - Sirocco the Dawn, Blast Held
   by a Tribute** - 2 of 4).
2. **Wrong legal scope/frequency on an effect that DOES activate.** The
   effect works, but who/what it may target, or how often it may be used,
   differs from the period rule. Covers **once-per-turn-name-lock (9)**,
   **target-legality (8)**, **cost-payment-behaviour (4)**, and the
   nomi-to-semi-nomi/Union sub-patterns within other-shared-ruling-era-change
   (**9** of 12).
3. **Trigger timing/registration differences.** WHEN a chain window opens
   changes, not WHETHER an action is possible. Covers
   **trigger-registration (3)**, **miss-timing-effect-flag-delay (1)**,
   **damage-step-activation-windows (2)**.
4. **Card-specific, severity varies per card** - the remaining
   **card-specific-errata (4)** and the 3 genuinely-distinct
   other-shared-ruling-era-change cards (Dark Necrofear, Evil HERO Dark Gaia,
   Necrovalley) each need individual severity judgement; none fit a general
   tier.

Tallying: **~40 cards** in tier 1 (functional lockout, the most severe class)
- and the 38-card leverage-priority #1 cluster is *also* the severity-tier-1
majority, so the single highest-leverage research target and the single most
severe behavioural-deviation class are the same cluster. That convergence,
not a popularity judgement, is the basis for the recommendation below.

## Recommended next milestone

**Not the 38-card web research. Design and implement independent-axis /
joint-state erratum modelling first.**

This document has now demonstrated a genuine structural contradiction
between what the data model claims and what a substantial slice of the
canonical data actually contains:

- the schema documents `changes[]` as a linear, ordered, oldest-to-newest
  version chain, and `selection_at()`'s candidate computation and
  `implementation_for_version()`'s lookup are both built on that assumption;
- **38 real erratum records** (confirmed individually, not sampled - see
  "Independent-axis C vs. ordinary-linear-chain C" above) intentionally
  contain two genuinely independent behavioural axes, not a chain, and say
  so in their own review notes;
- `selection_at()` has no way to represent the resulting joint-state space -
  for **29 of the 38**, its own candidate labels are actively
  self-contradictory (asserting a state the record's own dating already
  rules out), and the real "only one axis changed" state has no valid index
  at all, correct or otherwise;
- `implementation_for_version()` cannot map an implementation (or an
  explicit missing-implementation gap) to a joint state either - it can only
  address chain positions, and for 29 of the 38 records even that address is
  wrong.

Continuing to walk more formats chronologically, or spending a research pass
on any of the affected clusters, before this representation gap is closed
would keep building on a model that - for at least 38 cards today - either
mislabels its own output or cannot express the question being asked at all.
That is the more urgent problem this audit surfaced, ahead of any individual
chronology question.

**Recommend as the next milestone: design and implement independent-axis /
joint-state erratum modelling**, sized to be its own atomic task, with these
requirements:

- preserve ordinary linear chains exactly as they behave today - all 41 B
  records and all 6 ordinary-linear-chain C records must be unaffected;
- explicitly distinguish, per change, whether it is chained to its
  neighbour(s) or represents an independent axis (see the `"order":
  "chained" | "independent"` sketch under "Selection-model ordering
  question" above - a concrete starting point, not a final design);
- represent the possible joint behavioural states for a run of independent
  axes without abusing a linear prefix index the way `changes[0]`'s
  `resulting_implementation` slot is informally overloaded today;
- map an implementation, or an explicit and structured missing-implementation
  gap, to each historically-plausible joint state - not just to chain
  positions;
- `selection_at()` must return candidates whose labels are always
  semantically meaningful and never self-contradictory, for chained and
  independent-axis records alike;
- the validator must check the new representation (equivalent in spirit to
  today's `erratum.changes-out-of-order` check, extended to independent-axis
  runs);
- migrate the 38 currently-affected records, and audit the rest of the
  296-record corpus for the same shape before assuming it is unique to
  Edison's 85 - a quick scan during this revision found 46 records
  project-wide with an adjacent dated/undated relevant-change pair, of which
  2 (Insect Imitation, Last Will) are outside Edison's 44 known-wrong set;
  a first check suggests those 2 do not currently trigger the same broken-
  candidate symptom (their dated change is already confirmed NEW, not OLD,
  at a relevant snapshot), but this was not audited to the same depth as
  Edison's 44 and should be re-verified, not assumed, as part of the
  redesign;
- recompute every affected format's selection/warning counts once the
  migration lands, and confirm the 44/41/85 headline counts either hold or
  are explained;
- add regression tests for both true chains (propagation now applies
  correctly) and independent axes (joint-state candidates, not linear
  prefixes) - `tests/test_errata.py::OrderingConstraintTest` and
  `tests/test_repo_data.py::RealDataTest::test_giant_rat_selection_shape`,
  added by this audit to characterise *current* behaviour, would need
  re-authoring against the new, correct semantics once this lands.

**Not implemented in this commit** - it is not tiny or obviously safe, and
this commit's job was to make the audit and documentation truthful, not to
redesign the data model. Once that redesign lands, the 38-card (and 3-card
Cannon-lineage) chronology research recommended in earlier revisions of this
document becomes a well-founded follow-on milestone - the underlying
research value described above is real, it is simply premature to spend it
against a representation that cannot yet record the answer correctly for
29 of the 38 cards it would resolve.

Not started in this commit, per the task's explicit instruction.
