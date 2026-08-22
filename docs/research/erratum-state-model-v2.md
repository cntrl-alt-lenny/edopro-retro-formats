# Erratum state-model v2 — architecture research (roadmap item 5c follow-on)

**Scope: design only.** No canonical `data/errata/*.json` record changes, no
`retroformats/model.py`/`retroformats/validate.py`/`retroformats/lflist.py`
changes, no generated `dist/` changes, no schema changes committed in this
milestone. This document exists to choose an architecture and prove it
against real records before any implementation work is scheduled.

**Why now.** `docs/research/edison-behaviour-gaps.md` (commits 25cd7f4,
3e1a63b, c913817) established that the current data model — `changes[]` as a
single linear, ordered, oldest-to-newest chain — is structurally
insufficient for a real, non-trivial slice of the corpus: of the 44 Edison
C-partition records, 38 are two behavioural axes bundled into one historical
ruling with no evidenced order between them, and the other 6 pair one
undated change with a mechanically-unrelated dated one whose relative order
is also unevidenced. 29 of the 38 already produce self-contradictory
candidate labels *today*, at the one snapshot this project currently
queries; the rest can produce the identical failure at other snapshots this
project has not yet queried. Paladin of White Dragon has three relevant
changes spanning both relationship types in one record. Since this project
intends to reconstruct Yu-Gi-Oh! chronologically from the oldest formats
forward, every future format widens the set of snapshots queried against
this same data, and each new snapshot is a new opportunity for the same
class of bug to surface in a record that looks fine today only because no
one has queried it at the wrong date yet.

---

## 1. Domain model, before any schema

### Definitions

- **Behavioural transition.** One documented, dated-or-undated change from
  one card behaviour to another, at one point in the card's real-world
  history. A transition has a *kind* (functional / cosmetic / ruling /
  engine — only functional and ruling are implementation-relevant, matching
  today's `IMPLEMENTATION_RELEVANT_KINDS`), a *chronology* (exact date,
  bounded attestation, or completely unknown), and a description of what
  changed and why.

- **Behavioural axis.** A dimension of a card's behaviour that can move
  independently of other dimensions. Formally: a maximal totally-ordered
  chain of transitions, each one superseding the previous state of that
  *same* dimension. Two transitions belong to the same axis exactly when
  one is understood to be a later revision of the same underlying question
  the other addressed (e.g. "how does Necrovalley scope its negation" is
  one axis that moved through 4 dated states). Two transitions belong to
  *different* axes when they address different questions, even if one
  happens to constrain the other in practice (e.g. Giant Rat's
  reveal-on-whiff procedure and its activation-legality check are different
  questions, even though both concern "what happens when a search fails").

- **Historical state.** A complete, self-consistent assignment of a
  position to *every* axis simultaneously — a full description of one way
  the card could have behaved in play at some point in history. The
  baseline state (no transitions applied) and the modern state (every axis
  at its final position) are always states; every other combination
  reachable under the known ordering constraints is also a state.

- **Constraint between transitions.** A piece of evidence relating the
  possible timing of two transitions, either to each other or to absolute
  dates. Kinds actually present in this corpus: an exact `effective.date`;
  a bounded attestation (`old_attested_through` / `new_attested_from`); an
  explicit textual claim that one transition preceded or followed another;
  an explicit textual claim that the relative order is *not* known; and —
  the default, unstated case — no constraint at all.

- **Known-before / known-after relationship.** A specific constraint: from
  evidence (not from array position), transition A is known to have
  occurred strictly before transition B, or vice versa. This can come from
  dates (A's `new_attested_from` predates B's `old_attested_through`) or
  from a direct textual claim independent of dates.

- **Unknown relative order.** The absence of a known-before/known-after
  relationship between two transitions. This is the corpus's most common
  failure mode when it *does* occur (44 of 44 Edison C-partition records),
  and per the Edison audit, array position must never be read as evidence
  of it — only an explicit constraint (a date, or a stated claim) may
  establish order.

- **Genuinely independent transitions.** Transitions on different axes with
  unknown relative order *and* no reason to think their real-world timing
  is correlated — the joint state space is the full, unconstrained cross
  product of each axis's own positions. This is the general case; a
  "genuinely order-evidenced chain" (today's only correctly-modelled case)
  is the special case where every pairwise order happens to be evidenced.

- **Implementation coverage for a historical state.** The mapping from one
  historical state to what EDOPro artifact reproduces it: the modern
  `cards.cdb` entry, a reused upstream historical script, a
  project-authored custom script, an explicit "no reproduction needed"
  decision, a documented and acknowledged missing implementation, or an
  unresolved (not yet investigated) implementation question. Today this
  mapping is attached to *chain positions* (`implementation` for position 0,
  each change's `resulting_implementation` for position k); the redesign's
  central job is to attach it to *states* instead, since a state, not a
  chain position, is the thing an implementation actually reproduces.

- **Ambiguity at a format snapshot.** More than one historical state is
  consistent with the evidence at a given snapshot date. This is not a
  defect to be resolved by picking one — the whole point of `state:
  "ambiguous"` in the current model, correctly, is to refuse to guess.

### Is this a DAG, independent axes, explicit states, a hybrid, or something simpler?

**Answer: a hybrid — (A) transitions with a partial order for chronology,
plus (C) explicit state-keyed implementation coverage for the mapping to
EDOPro artifacts. Axis (B) is not a fourth structure; it is a *derived*
view of (A)'s structure, useful for documentation and for keeping
authoring simple in the common case, but not something the underlying
computation needs as a separate primitive.**

The reasoning that leads here, worked through explicitly since the task
asks not to assume it:

1. Chronology is fundamentally a question about **order**, not about
   labelled dimensions. What `selection_at()` actually needs to compute, at
   a snapshot, is "which sets of transitions could plausibly have all
   occurred, together, by this date, and no others" — that is a
   partial-order / DAG query (an *order ideal*, in the mathematical sense:
   a down-closed subset of a partial order) over transitions, not
   fundamentally an axis query. Architecture (A) answers this directly.

2. "Axis" turns out to be *redundant* with a special case of (A): a
   maximal chain in the DAG (a totally-ordered run of transitions with no
   branching) already behaves like today's schema, no matter what it is
   called. Modelling "axis" as a first-class schema construct (candidate
   architecture 2 below) is a legitimate, simpler-to-author *encoding* of
   the same underlying DAG for the common single-axis case, but it is not
   a structurally different answer to the chronology question — see §6.

3. Implementation coverage is a **separate problem** from chronology, and
   trying to answer it by attaching data to transitions (as today's
   `resulting_implementation` does) is precisely what breaks once more than
   one transition can be simultaneously "the most recent thing that
   happened" (i.e. once the DAG is not a single chain). A transition
   creates a *boundary*, not a state; a state is what an implementation
   actually reproduces. So implementation coverage must be keyed by state
   — explicit-state architecture (C) — layered on top of whatever produces
   the state space, whether that is (A)'s DAG or (B)'s axis cross-product.

4. Nothing simpler (E) survives contact with Paladin of White Dragon (three
   relevant changes, two relationship types in one record) or with the
   discovery that `changes[]` list order is not reliable evidence even for
   two-change records (29 of the 38 Edison cluster-1 records have their
   axes in the "wrong" order for today's linear-index arithmetic to work
   coincidentally). Any representation smaller than "an explicit,
   evidence-only order relation between transitions, plus explicit
   per-state implementation coverage" either reintroduces a hidden
   assumption (list order, a two-valued global flag) or cannot express a
   partially-ordered three-transition record like Paladin's.

This is the answer the rest of this document builds from. It also explains
why, of the three architectures developed below, the recommendation (§13)
ends up being closest to Architecture 1 — but all three are worked through
fully first, on their own terms, per the task's explicit instruction not to
skip that comparison.

---

## 2. Three candidate architectures

All three are genuinely different mechanisms, not stylistic variants:
Architecture 1 treats transitions as the primitive and derives states from
an explicit order relation; Architecture 2 treats axes as the primitive,
mandatory and declared up front, and derives states from a cross product;
Architecture 3 treats states as the primitive and does not store
transitions at all. A fourth, deliberately *smaller* idea (a two-valued
per-change ordering flag) is discussed in §12 as the "something simpler"
option the task asks not to skip — it is not developed as a full
architecture because it fails the very first stress case (Paladin) badly
enough that carrying it through all eleven comparison points below would
mostly repeat that failure.

### Architecture 1 — Transition partial order + explicit state map

**Core idea.** Store transitions with an explicit, evidence-only
predecessor relation (`after: [transition_id, ...]`, defaulting to "the
previous entry in the list" for authoring convenience, but overridable —
critically, `after: []` on a non-first entry is how a record declares "not
chained to what precedes it," the escape hatch today's schema has no way to
express). Store implementation coverage separately, keyed by the *set* of
transition ids applied, not by chain position.

**Canonical data shape:**

```jsonc
{
  "id": "erratum-giant-rat",
  "modern_card": { "passcode": 97017120, "name": "Giant Rat" },
  "classification": "ruling",
  "transitions": [
    {
      "id": "verification",
      "kind": "ruling",
      "after": [],                 // no known predecessor
      "effective": { "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03" },
      "summary": "Deck-reveal-on-whiff procedure..."
    },
    {
      "id": "activation-semantics",
      "kind": "ruling",
      "after": [],                 // ALSO no known predecessor -- not "after: [verification]"
      "effective": { "date": null },
      "summary": "No-valid-target activation allowance..."
    }
  ],
  "states": [
    { "applied": [], "implementation": { "strategy": "reuse-upstream", "historical_passcode": 504700172 } },
    { "applied": ["activation-semantics"], "implementation": { "strategy": "unresolved", "gap": {...} } },
    { "applied": ["verification"], "implementation": null, "unattested": true },
    { "applied": ["verification", "activation-semantics"], "implementation": "modern" }
  ]
}
```

`"applied": [...]` is always a *down-set* of the `after` relation — a state
that requires transition B applied must also have every transition B's
`after` names applied. The build/validator generates the full set of valid
down-sets mechanically from the transitions and their `after` edges; an
author writes `states[]` entries only for the ones that need an
implementation record different from the mechanical default (see §10 for
what the default is and why an unauthored-but-reachable state must not
silently mean "modern").

**Selection algorithm.** For a snapshot: compute each transition's
OLD/NEW/AMBIGUOUS state exactly as `change_state_at()` does today. A
down-set is a *candidate* at this snapshot iff every transition it contains
is NEW-or-AMBIGUOUS and every transition it excludes is OLD-or-AMBIGUOUS,
**and** it respects `after` (already true if it is a valid down-set at
all). Collect all candidate down-sets; look each one up in `states[]`
(falling back to the documented default policy for unauthored-but-reachable
ones). If exactly one candidate: determinate. If more than one: ambiguous,
with the *set of states*, not integers, as the candidate list.

**Implementation lookup.** Direct: `states[]` keyed by the down-set,
independent of how many transitions or axes are involved.

**Ambiguity representation.** The set of down-sets consistent with the
per-transition OLD/AMBIGUOUS/NEW evidence at the snapshot — see §9 for the
concrete replacement of `ErratumSelection`.

**Validator invariants (preview; full list in §10).** `after` must
reference only earlier-declared transition ids (no cycles by construction
if enforced at parse time); every state's `applied` set must be a valid
down-set; the down-set consisting of every transition must map to `"modern"`
and no other down-set may; a down-set whose per-transition dating produces
a *definite* contradiction (e.g. B's `after` names A, but B's
`new_attested_from` predates A's `old_attested_through`) is rejected —
this generalises today's `erratum.changes-out-of-order` check from "the
whole list" to "each `after` edge."

**Migration complexity.** Every single-transition record (236 of 296) is a
one-line rename (`changes[0]` becomes `transitions[0]`, `implementation`
becomes `states[0].implementation` for the baseline down-set `[]`, the
final `resulting_implementation`-less state is implicitly `"modern"`) —
this is close to a mechanical, non-semantic transform. Every fully-dated
multi-transition record (the bulk of the other 60) keeps its existing
transition order as the default `after` chain, unchanged in meaning — also
close to mechanical. Only the ~44 records this document has already fully
audited (plus whatever the corpus-wide re-audit in §7 finds) need a human
to add `after: []` and split the flat `resulting_implementation` chain into
explicit `states[]` entries.

**Computational complexity.** For `k` relevant transitions, the down-set
count is bounded by 2^k in the fully-independent case and by `k+1` in the
fully-chained case; real records never exceed `k=4` (see the corpus scan in
§7), so 2^4=16 is the realistic worst case, negligible. Selection at a
snapshot is O(2^k) in the worst case (enumerate down-sets, filter by
per-transition state) — for realistic `k` this is imperceptible; §12
returns to whether this could ever matter.

**Human-authoring ergonomics.** Best case (single axis, which covers the
overwhelming majority of the corpus) is as simple as, or simpler than,
today's schema — no `after` needed at all if the default (chain to the
previous entry) is accepted. Worst case (Giant-Rat-shaped genuine
independence) requires one explicit `"after": []` annotation plus an
explicit `states[]` array instead of one `resulting_implementation` field —
more verbose than today, but the verbosity is exactly proportional to the
genuine complexity being described, not incidental.

**Excluding contradictory/impossible states.** Structurally, by
construction: a down-set that is not down-closed under `after` is not a
valid state at all, so "verification NEW alone" (Giant Rat's impossible
candidate today) is simply never generated as a down-set unless
`verification` has no predecessor requirement blocking it — which is
exactly right, since nothing *does* block it in the abstract; what excludes
it *at the Edison snapshot specifically* is the per-transition dating
filter (verification is confirmed OLD at Edison, so any down-set containing
it is filtered out at that snapshot), not a structural impossibility. This
is the correct behaviour: distinguishing "structurally impossible" from
"ruled out at this particular snapshot" is exactly the distinction the
current model conflates.

**Scaling 1 → 2 → 3+ transitions.** 1: trivial, `states[]` has 2 entries
(baseline, modern), no `after` needed. 2: today's linear case if dated and
chained (`after` defaults correctly); Giant Rat's case if independent
(`after: []` on the second, 4 down-sets, 2 of them typically authored). 3+:
Paladin — three transitions, two of them (activation, verification) with
`after: []` relative to each other, the third (2013 attack-restriction)
also `after: []` relative to both (order versus them is unevidenced too,
per the Edison audit) — 8 combinatorial down-sets total, of which the
snapshot filter at Edison narrows to exactly the 2 the current ad hoc
3-relevant-change computation already (accidentally) gets right; see §3.C
for the full worked trace.

**Backwards-compatibility implications.** See §8; this architecture is the
one evaluated there as "normalise both forms internally," since its data
shape for the simple case is close enough to today's to make a dual-read
period cheap.

**Failure modes.** Authors forgetting `after: []` on a genuinely
independent transition silently reintroduces today's bug in the *new*
schema — this must be caught by a validator heuristic (§10: an undated
transition whose default `after` chains it to a transition confirmed at a
much later date, with review notes using language like "cannot be
sequenced," is flagged for a human to confirm the `after` edge is
intentional). `states[]` entries that reference a down-set the DAG cannot
actually produce (typo in transition ids) must be a validator error, not a
silent no-op.

### Architecture 2 — First-class independent axes, cross-product states

**Core idea.** Make "axis" a mandatory, explicit schema construct rather
than an emergent property. Each record declares one or more named axes; each
axis is an ordinary, always-chained sequence of transitions (today's schema,
verbatim, *scoped to one axis*); cross-axis ordering is stated only when
evidenced, defaulting to "unordered." States are keyed by a tuple of
per-axis positions.

**Canonical data shape:**

```jsonc
{
  "id": "erratum-giant-rat",
  "axes": [
    {
      "id": "verification",
      "transitions": [
        { "effective": { "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03" }, "summary": "..." }
      ]
    },
    {
      "id": "activation-semantics",
      "transitions": [
        { "effective": { "date": null }, "summary": "..." }
      ]
    }
  ],
  "axis_order": [],   // e.g. [{"before": "verification@0", "after": "activation-semantics@0"}] if ever evidenced
  "state_implementations": {
    "verification=0,activation-semantics=0": { "strategy": "reuse-upstream", "historical_passcode": 504700172 },
    "verification=0,activation-semantics=1": { "strategy": "unresolved", "gap": {...} },
    "verification=1,activation-semantics=0": null,
    "verification=1,activation-semantics=1": "modern"
  }
}
```

**Selection algorithm.** Per axis, run *today's* linear-chain algorithm
unmodified (each axis, by construction, is a valid chain) to get a
per-axis candidate range. Cross-product the per-axis candidate ranges,
minus any combination `axis_order` rules out. Look up each surviving tuple
in `state_implementations`.

**Implementation lookup.** A flat map keyed by the tuple string (or,
structurally, a nested dict) — direct, same complexity as Architecture 1.

**Ambiguity representation.** The set of surviving axis-position tuples.

**Validator invariants.** Every axis must independently satisfy today's
`erratum.changes-out-of-order` check (unchanged, scoped per-axis); every
`axis_order` entry must reference real axis positions; `state_implementations`
keys must be exactly the reachable tuples, no more, no fewer than what the
cross product (minus `axis_order` exclusions) produces; the
all-axes-at-final-position tuple must map to `"modern"`.

**Migration complexity.** The 236 single-transition and the fully-dated
multi-transition records: identical to Architecture 1's migration story —
essentially a rename, since "one axis, N chained transitions" is exactly
what most records already are. The Edison-shaped records need one *new*
concept per record — declaring 2 (or 3, for Paladin) separate `axes[]`
entries instead of one `changes[]` array — which is a more visible
restructuring than Architecture 1's `after: []` annotation, but arguably
clearer to a reader unfamiliar with the record (the axis split is explicit
in the shape of the JSON, not a flag buried in one field).

**Computational complexity.** Identical to Architecture 1 in the worst
case (same 2^k bound for k independent single-transition axes), but
typically *smaller* in practice for axes with multiple internal
transitions, since each axis's own candidate range is computed once via
cheap O(n) linear-chain arithmetic before the cross product, rather than
enumerating raw transition subsets.

**Human-authoring ergonomics.** The single best-case ergonomics of the
three for the *overwhelming majority* of the corpus — a record with one
axis is *unchanged* from today's schema in spirit (rename `changes` to
`axes[0].transitions`, or make the single-axis case elidable entirely, see
§8). The Edison-shaped 10% is more work than Architecture 1's single-flag
fix, because the author must name and structurally separate the axes, but
that work is arguably *the actually necessary intellectual work* the
original authoring should have done in the first place (Giant Rat's
"verification" and "activation-semantics" are genuinely two questions; the
schema forcing them into two named axes is arguably a feature, prompting
the question "is this really one thing or two?" that the old schema never
asked).

**Excluding contradictory/impossible states.** Structurally, by
construction, in the same way as Architecture 1 — a tuple is only
considered if every axis's own linear-chain arithmetic already allows the
corresponding position, so no axis position can ever be "skipped" or
reached out of its own internal order.

**Scaling 1 → 2 → 3+.** 1 axis: today's schema. 2 axes, both single-
transition: Giant Rat, above. 3+ transitions/axes: Paladin needs 3
single-transition axes (activation, verification, attack-restriction) with
an empty `axis_order` (no cross-axis order evidenced for any pair) — 8
combinatorial tuples, same count as Architecture 1, same snapshot-filtered
result; see §3.C.

**Backwards-compatibility implications.** A record with exactly one axis
IS today's schema under a thin rename — the cleanest of the three for a
"schema v2, but v1 records still validate as a degenerate case" story (§8
option B/D boundary).

**Failure modes.** Authors mis-drawing axis boundaries — declaring two
transitions as separate axes when they are actually the same evolving
question (or vice versa) — is a *modelling* error this schema makes
*visible* (a reviewer can ask "why are these two axes and not one chain?")
but cannot mechanically detect; the validator can only check internal
consistency, not whether the axis split matches reality. This is a
genuine, not merely cosmetic, difference from Architecture 1, where
"independent" is a flag on an edge, easier to get away with leaving wrong
silently since it doesn't force a structural split.

### Architecture 3 — Explicit historical states, transitions not stored

**Core idea.** Do not model transitions or axes at all. A record is
directly a list of named historical states, each carrying its own
plausibility evidence and its own implementation. "Transition" becomes an
implicit, unstored concept — the boundary between two states a human
happens to describe consecutively in prose, not a thing the schema tracks.

**Canonical data shape:**

```jsonc
{
  "id": "erratum-giant-rat",
  "states": [
    {
      "id": "goat-baseline",
      "description": "Reveal-on-whiff required; no target check at activation.",
      "plausible_when": { "on_or_before": "2011-02-02" },
      "implementation": { "strategy": "reuse-upstream", "historical_passcode": 504700172 }
    },
    {
      "id": "activation-tightened-only",
      "description": "Reveal still required; activation now needs a valid target.",
      "plausible_when": { "unknown": true },
      "implementation": { "strategy": "unresolved", "gap": {...} }
    },
    {
      "id": "modern",
      "description": "Neither reveal nor unconditional activation.",
      "plausible_when": { "on_or_after": "2019-04-03" },
      "implementation": "modern"
    }
  ]
}
```

Note what is *missing* relative to Architectures 1-2: the fourth
theoretically-generatable state ("verification NEW, activation OLD") is
simply never written down, because no evidence suggests it is worth
tracking. This is the central, defining difference of this architecture —
completeness is an authoring discipline, not a mechanical guarantee.

**Selection algorithm.** For a snapshot, evaluate each state's
`plausible_when` predicate directly — no derivation, no down-set
enumeration. Zero matches is an authoring gap (validator error: the state
space is not exhaustive at this snapshot). One match is determinate. Two or
more is ambiguous, with those states as candidates.

**Implementation lookup.** Trivial — it is inline on the matching state(s),
there is no separate lookup step at all.

**Ambiguity representation.** The list of states whose `plausible_when`
predicate is simultaneously satisfiable at the snapshot.

**Validator invariants.** Every snapshot in every format this project
defines must match at least one state for every reviewed record with
relevant states (this is checkable only empirically, by evaluating every
state against every format's snapshot — there is no structural
completeness guarantee the way a down-set enumeration provides one "for
free"); state ids must be unique; exactly one state may be unconditionally
`"modern"`; `plausible_when` predicates must not both structurally require
and structurally forbid the same absolute date range (a much weaker check
than Architecture 1/2's cycle/contradiction detection, because there is no
shared structural skeleton to check consistency against).

**Migration complexity.** Best for the ~236 trivial one-transition records
*if* a mechanical "baseline state + modern state" template is used — but
this is not obviously less work than Architecture 1/2's rename, and for
records with 2+ dated transitions, a human must manually re-author N+1
`plausible_when` predicates in absolute-or-relative-date terms, rather than
the migration mechanically deriving them from existing `effective` fields
— strictly more migration work than Architecture 1/2 for the 60
multi-transition records, because the derivation Architecture 1/2 get for
free (down-set validity implies plausibility) has to be hand-authored here.

**Computational complexity.** O(number of authored states) per snapshot
query — typically *smaller* in the well-behaved case than Architecture
1/2's O(2^k), since only plausible states are ever written down at all, but
this saving is illusory: it is bought by *not* mechanically enumerating
the full space, which is also why completeness is not guaranteed.

**Human-authoring ergonomics.** Excellent for a human historian's natural
mental model — "this card had 3 known eras, here they are, here's what
distinguishes them" reads like a research note, not a data structure. Poor
for correctness assurance: nothing stops an author from writing 2 states
that jointly leave the true history of some snapshot uncovered, and
nothing *generates* the states an author should consider, unlike
Architecture 1/2 mechanically producing "here are the 2^k combinations,
which have you accounted for."

**Excluding contradictory/impossible states.** Entirely by omission — an
"impossible" state such as Giant Rat's "verification NEW, activation OLD"
at Edison is excluded only because no one wrote it down, not because the
schema understands why it is excluded. This is fragile: it relies on the
author correctly intuiting, every time, which combinations don't need
representing, rather than the schema refusing to generate the impossible
ones. For Giant Rat specifically it works, precisely because a human
(this project's own prior authoring) already reasoned it through — but that
reasoning left no structural trace for the validator to check against.

**Scaling 1 → 2 → 3+.** 1 transition: 2 states (baseline, modern), no
harder than today. 2 transitions, independent: up to 4 states, of which an
author may reasonably choose to write only the plausible-looking ones (as
above) — cheapest of the three architectures to author *if* the author's
judgement about which combinations matter is correct, and silently
wrong if it is not. 3+ transitions (Paladin): up to 8 states in principle;
in practice a human would likely author far fewer, by reasoning "the 2013
attack-restriction is independently dated and irrelevant to the
verification/activation pair below its own date" — which is exactly the
kind of judgement call this architecture asks a human to get right every
time, with no mechanical check.

**Backwards-compatibility implications.** Weakest of the three — today's
schema has no state concept at all, so migrating means re-deriving
`plausible_when` predicates for every existing `effective` field by hand,
which is strictly more manual work than a mechanical rename.

**Failure modes.** Silent state-space gaps (a real historical possibility
that no one thought to author, discovered only when a future format's
snapshot lands inside it and the validator's empirical
every-snapshot-covered check catches it — or doesn't, if that format is
added later without re-running the check against every existing record).

---

## 3. Proof against real records

Nine real records, not seven — the two extra were found while doing the
corpus-wide scan for §7 and are kept here because each stresses a shape the
task's own seven cases do not: **YZ-Tank Dragon** has two relevant changes
that are *both* completely undated (unlike every Edison case, where exactly
one side was dated), so nothing pins either axis at any snapshot; **Insect
Imitation** / **Last Will** have an order claim that is neither a raw date
nor an explicit "unknown" disclaimer, but a researcher's stated inference
("the functional change precedes the ruling change") — a third evidence
tier the task's own examples do not surface. All nine are worked through
for Architecture 1; Architectures 2 and 3 are shown wherever they differ in
substance from Architecture 1, and only in their data shape where the
computed answer is identical (which is most cases — the three
architectures agree on *what* the candidate set is far more often than
they differ in *how it is written down*).

### A. Giant Rat — the baseline stress case

Two changes, `verification` dated (`old_attested_through: 2011-02-02`),
`activation-semantics` completely undated. At Edison (2010-04-24):

| Architecture | Result |
|---|---|
| 1 (DAG) | `after: []` on both. Down-sets: `{}`, `{activation}`, `{verification}`, `{verification, activation}`. At Edison, `verification` is OLD (excluded), `activation` is AMBIGUOUS (either). Surviving down-sets: `{}` and `{activation}`. Candidates = **2 states**: baseline (implemented, 504700172) and "activation alone" (unresolved gap). `{verification}` alone is never generated as a candidate at this snapshot — not because it is structurally forbidden, but because `verification`'s own dating rules it out here specifically. |
| 2 (axes) | Two single-transition axes, `axis_order: []`. Per-axis: `verification` pinned at position 0 (OLD, definite); `activation-semantics` ranges over {0, 1} (AMBIGUOUS). Cross product minus impossible combinations = same 2 tuples as Architecture 1: `(0,0)` and `(0,1)`. |
| 3 (states) | Author writes exactly the 2 states that matter (`goat-baseline`, `activation-tightened-only`) with `plausible_when` predicates that both evaluate true at 2010-04-24 (the former's date-bound is satisfied, the latter's `unknown: true` is always satisfiable). Same 2-candidate answer, but because the author chose to write only 2 of the 4 combinatorially possible states, not because the schema derived it. |

All three produce the same 2-state answer this project has already
committed to (c913817). Architectures 1 and 2 derive it mechanically;
Architecture 3 reproduces it only because a human already reasoned it out
correctly when authoring — nothing in Architecture 3 would have caught it
if they hadn't.

### B. A Deal with Dark Ruler — reversed list order relative to Giant Rat

Same two axes as Giant Rat, but `changes[]` lists `activation-semantics`
first and `verification` second — one of the 8 records (per the Edison
audit) where this reversal happens to make today's linear-index arithmetic
accidentally land on the right answer.

| Architecture | Result |
|---|---|
| 1 (DAG) | Authoring order is irrelevant — `after: []` is declared per-transition, not inferred from array position. Same down-set computation as Giant Rat, same 2 surviving candidates, **regardless of which transition object is written first in the JSON array.** |
| 2 (axes) | `axes[]` order is likewise irrelevant — cross product is computed over axis identity, not array position. Same 2-tuple answer. |
| 3 (states) | States are named, not positioned — order is not even a concept here. Same 2-state answer. |

This is the point of the exercise: under all three architectures, **the
authoring order of `A Deal with Dark Ruler`'s two changes and `Giant Rat`'s
two changes can be swapped without changing either record's computed
answer** — eliminating the exact defect that made 29 of the 38 Edison
records self-contradictory while the other 9 happened to work by
accident. Today's schema is the only one of the four designs discussed in
this document (three here, plus today's) whose answer depends on list
order at all.

### C. Paladin of White Dragon — three changes, mixed relationships

Three relevant changes: `activation` (undated), `verification` (bounded
2011-02-02 / 2019-04-03), `attack-restriction` (dated exactly 2013-09-13,
mechanically unrelated to the other two). `activation`/`verification` are
a bundled pair (Giant-Rat-shaped); `attack-restriction` has unevidenced
order relative to both of them, but its own exact date pins its own state
at any snapshot regardless.

| Architecture | Result |
|---|---|
| 1 (DAG) | Three transitions, all `after: []` (no pairwise order evidenced among any of the three). 8 combinatorial down-sets. At Edison: `verification` OLD, `attack-restriction` OLD (2010 < 2013), `activation` AMBIGUOUS. Surviving down-sets: `{}` and `{activation}` — exactly 2, because both `verification` and `attack-restriction` being confirmed OLD excludes every down-set containing either of them, leaving only the two that vary solely in `activation`. Matches the live `selection_at()` output already verified for this record (`candidates=(0,1)`, `state=ambiguous`). |
| 2 (axes) | Three single-transition axes, empty `axis_order`. Per-axis ranges: `verification`={0}, `attack-restriction`={0}, `activation`={0,1}. Cross product = 2 tuples, same answer. |
| 3 (states) | An author would need to reason through all 8 combinations by hand (or explicitly decide, as the real record's review notes do, that `attack-restriction` is "not reachable by either in-scope snapshot" and simplify to 2 states up front) — same 2-state answer *if* the author's manual reasoning is as careful as it was for the real record, with no structural check that it was. |

This is the key stress case for any design that only handles two-change
records: a two-valued `chained | independent` flag on `changes[]` (the
"something simpler" option flagged for rejection in §12) has no way to
express "these two are unordered, and this third one is *also* unordered
relative to both, but for an unrelated reason and with its own,
independently-dated pin." All three real architectures handle it because
none of them assumes exactly two transitions.

### D. Tyrant Dragon — mechanically-distinct, order genuinely unknown

Two changes: `extra-attack-condition` (undated), `revival-tribute-timing`
(dated exactly 2013-10-11), mechanically unrelated (an attack condition and
a Graveyard-revival cost timing). `review.notes`: *"cannot be sequenced
against each other because the former has no chronology at all."*

| Architecture | Result at Edison (2010-04-24) |
|---|---|
| 1 (DAG) | `after: []` on both (no order evidenced — the explicit disclaimer is exactly the signal that should suppress the "chain to previous entry" default, see §10's validator heuristic). Down-sets: `{}`, `{extra-attack}`, `{revival-timing}`, both. `revival-timing` confirmed OLD (2010 < 2013) excludes any down-set containing it. Surviving: `{}` and `{extra-attack}` — 2 candidates, `implementation_for_version(1)`-equivalent has no recorded implementation, matching this project's already-committed C classification. |
| 1 (DAG), snapshot 2014-01-01 | `revival-timing` now confirmed NEW. Surviving down-sets: `{revival-timing}` and `{extra-attack, revival-timing}` (modern) — 2 candidates, **not** a self-contradiction, because nothing in the DAG ever asserted `extra-attack` had to happen relative to `revival-timing` in either direction; the down-set `{revival-timing}` alone is a perfectly valid, always-available state. This is where today's schema, evaluated at this same later snapshot, produces a self-contradictory candidate (verified directly against live code in the Edison audit) — the new architecture does not reproduce that bug at *any* snapshot, which today's schema-plus-list-order cannot claim. |
| 2 (axes) | Identical result under the cross-product formulation — two single-transition axes, empty `axis_order`, same 2-candidate answer at both snapshots. |
| 3 (states) | An author would write states keyed to `revival-timing`'s date directly (e.g. "pre-2013-10-11, extra-attack unknown" / "post-2013-10-11, extra-attack unknown") — same answer, again contingent on the author correctly reasoning that no order claim should be encoded. |

### E. Axe of Despair — the second order-unknown, mechanically-distinct case

Structurally identical to Tyrant Dragon (undated ruling + unrelated dated
2013 functional change), except the record's own review notes never
explicitly say "cannot be sequenced" — they are simply silent on order,
which the Edison audit already established is not evidence of order
either. All three architectures produce the identical result to Tyrant
Dragon's, because none of them treats textual silence as an "after" edge
by default — the DAG's default is "no known predecessor," not "chained
unless disclaimed."

### F. Necrovalley — genuinely fully-dated multi-change record

Four changes, every one carrying a real, specific `effective.date`. This
is the case that must **not** become more cumbersome under the redesign.

| Architecture | Result |
|---|---|
| 1 (DAG) | Default `after` (each transition implicitly follows the previous list entry) needs **zero explicit annotation** — the record is unchanged in spirit from today's schema. Down-set enumeration collapses to exactly `k+1` linear states because every pairwise order is dated, identical to today's `k_min..k_max` arithmetic. |
| 2 (axes) | One axis, four chained transitions — literally today's schema, renamed. |
| 3 (states) | Requires re-deriving 5 `plausible_when` predicates from the 4 dates by hand — the one case where Architecture 3 is *more* authoring work than today, not less, because nothing mechanically derives a state predicate from a transition date the way down-set validity does in Architectures 1/2. |

### G. A one-change record (the common case — e.g. any of the 236 trivial records)

| Architecture | Result |
|---|---|
| 1 (DAG) | One transition, two down-sets (`{}`, `{it}`) — `baseline_implementation` and `"modern"`. No `after` needed at all. |
| 2 (axes) | One axis with one transition — indistinguishable from Architecture 1 for this case. |
| 3 (states) | Two states, `plausible_when` mirrors the single `effective` block directly — also trivial, and arguably marginally more direct to read than the other two for exactly this simplest case. |

All three keep the simple case simple; none of the added machinery for
multi-transition records leaks into a one-change record's shape.

### H. YZ-Tank Dragon — both changes completely undated (bonus case)

Two changes — a Monster-Zone contact-material restriction and a
nomi-vs-semi-nomi summoning-condition change — **neither** carrying any
date or bound at all. The record's own review notes state outright:
*"The relative order of the two recorded changes is also unknown; they are
chained ruling-then-functional for continuity"* — a first-party admission,
independent of anything this document argues, that this project's own past
authoring has used `changes[]` list order as a narrative convenience with
no evidentiary weight, exactly the failure mode this whole redesign exists
to close off.

| Architecture | Result at any snapshot before both changes' (unknown) dates |
|---|---|
| 1 (DAG) | `after: []` on both. All 4 down-sets survive (both transitions AMBIGUOUS, nothing pins either) — **4 candidates**, the largest candidate set among the worked examples, correctly reflecting that this record currently has the least evidence of any real record in the corpus. |
| 2 (axes) | Same 4-tuple cross product. |
| 3 (states) | An author would need to decide, unprompted, whether to write 2, 3, or 4 states — the review note's own "chained... for continuity" phrasing shows the *actual* author reached for a linear chain out of habit even while writing, in the same paragraph, that no order is known. This is the sharpest illustration in the corpus of why Architecture 3's correctness depends entirely on authoring discipline that even this project's own most careful reviewer did not consistently apply. |

### I. Insect Imitation / Last Will — a researcher-asserted order claim

Two changes each: one exactly dated (2009-07-24 / 2005-11-01), one
completely undated. Unlike every other undated-pair case above, the review
notes do not say "unknown" or "cannot be sequenced" — they assert a
conclusion: *"the position erratum is anchored to a 2009 printing while the
verification procedure is attested in force through 2011-02-02, so the
functional change precedes the ruling change."* This is neither a raw date
nor a disclaimed unknown — it is a **researcher's own inference**,
stated as fact but not directly sourced the way an `effective.date` is.

None of the three architectures developed above has a first-class way to
express "ordered, but by inference rather than by direct date" — all three
would currently have to either (a) treat it as evidenced order (an
explicit `after` edge / axis-order entry / a `plausible_when` predicate
built assuming the order) on the strength of the researcher's stated
reasoning, or (b) decline to encode an order at all and fall back to the
`mechanically-distinct-order-unknown` treatment out of caution. This
project's migration workflow, asked to classify this record without
further guidance, chose caution (`needs-manual-review`, see §7) rather than
either extreme — which this document treats as the correct call: **the
redesign's constraint vocabulary (§5) needs a distinct tier for
"order asserted by domain reasoning, not by a dated source,"** so a future
author can record *why* the order is believed without silently promoting
it to the same evidentiary weight as a citation, or silently discarding it
as if it were as weak as list position. This is a real gap the task's own
seven prescribed cases did not surface, and is called out explicitly rather
than papered over with a forced classification.

---

## 4. Implementation mapping is a first-class problem

Restating the task's own 2×2 for Giant Rat's two axes:

```
              Activation
              OLD              NEW
Ver   OLD   A: 504700172     B: missing (unresolved)
      NEW   C: never happens  D: modern (cards.cdb)
            at Edison (C's
            own dating rules
            it out here)
```

None of the three architectures needs a linear index to say this. In
Architecture 1, `A` is `states[{"applied": []}]`, `B` is
`states[{"applied": ["activation"]}]`, `C` would be
`states[{"applied": ["verification"]}]` (present in the schema, simply
never a candidate at the Edison snapshot — see §3.A), `D` is the
all-transitions-applied state, hard-required to be `"modern"`. In
Architecture 2, the same four cells are the four `(verification-position,
activation-position)` tuples. In Architecture 3, only the cells an author
chooses to write down exist at all — which for Giant Rat happens to be
exactly `A`, `B`, and `D`, but nothing prevents an author from forgetting
one.

**The six implementation kinds must all be expressible per state, not
per record:**

| Kind | Today (`implementation.strategy`) | State-keyed equivalent |
|---|---|---|
| Modern implementation | *(implicit: version ≥ len(relevant))* | the terminal state's implementation is always `"modern"`, structurally |
| Reuse-upstream historical | `strategy: "reuse-upstream"` | unchanged shape, just attached to a state key instead of a chain position |
| Custom implementation | `strategy: "custom-script"` | unchanged shape, same reattachment |
| None-needed | `strategy: "none-needed"` | unchanged shape, same reattachment |
| Known missing implementation | `strategy: "unresolved"` + `gap: {...}` | unchanged shape, same reattachment — this is exactly state `B` above |
| Unresolved investigation | `strategy: "unresolved"`, no `gap` | unchanged shape — the validator must still require *either* a real implementation *or* a `gap` acknowledgement per **reachable** state, exactly like today's `erratum.modern-implementation-recorded` / gap-acknowledgement checks, just evaluated per state instead of per chain position |

**Scaling beyond two binary axes** is mechanical in Architectures 1/2 (the
down-set count / tuple space grows with the transitions actually present —
§7's corpus scan finds nothing beyond 4 relevant transitions in any real
record today, so the practical ceiling is 16 states, not a runaway
combinatorial concern) and manual in Architecture 3 (an author enumerating
states for a hypothetical 4-independent-axis record would have to write up
to 16 entries by hand, with no mechanical prompt telling them how many they
should have).

---

## 5. Historical constraints

The constraint vocabulary a snapshot-selection algorithm must be able to
consume, derived from what the corpus actually contains (§3, §7) rather
than invented in the abstract:

1. **Exact transition date** (`effective.date` + `precision`) — today's
   strongest, most common evidence kind; unchanged in the new model.
2. **Bounded attestation** (`old_attested_through` / `new_attested_from`)
   — unchanged; this is what pins Giant Rat's `verification` axis at
   Edison without pinning an exact date.
3. **Explicit known-before/known-after between two named transitions**
   — new. Needed whenever order is evidenced by something other than dates
   (a direct cross-reference in a period document, or — see (6) below — a
   researcher's stated inference). Represented as the `after` edge
   (Architecture 1) or an `axis_order` entry (Architecture 2).
4. **Explicit "relative order is unknown"** — new, and importantly a
   *positive* assertion, not merely the absence of (3). The corpus already
   writes this in prose for 42 of the 44 Edison C-partition records (four
   Edison non-cluster records plus, per §7's re-audit, most of the newly
   classified `mechanically-distinct-order-unknown` and
   `bundled-independent-axis` records use language to this effect); the new
   schema should let this be recorded structurally (`after: []` with a
   `reason` string, or equivalent), not left to review-note prose the
   validator cannot check.
5. **Two transitions known to belong to separate axes** — the substantive
   claim underlying the `bundled-independent-axis` category: not just "we
   don't know the order," but "these describe genuinely different
   questions a single upstream script happens to answer together." This is
   a *labelling* fact more than a *constraint* fact (it does not change the
   computed candidate set relative to plain "order unknown" — see §3.A vs
   §3.D, which compute identically) — its value is entirely for §7
   migration bookkeeping and human documentation, which is exactly why §1
   concluded axis is not a separate computational primitive.
6. **Order asserted by researcher inference, not by a direct source** —
   new, surfaced by Insect Imitation / Last Will (§3.I) and not otherwise
   present in the corpus in this exact form. Recommendation: give this its
   own `basis` field (parallel to `effective.basis`) so the inference is
   visible and auditable rather than indistinguishable from either a hard
   date or an unevidenced guess. Whether to treat it as strong enough to
   license an `after` edge, or weak enough to fall back to (4), is a
   judgement call this document deliberately leaves to the eventual
   reviewing author on a per-record basis (see §7's manual-review flag for
   these two records) rather than prescribing here.
7. **Two transitions potentially occurring together** — mentioned by the
   task as a possibility "if the evidence ever supports it." No record in
   this corpus currently asserts simultaneity as opposed to unknown order;
   the schema should not forbid it (a same-`effective.date` pair should be
   a legal, if unusual, input — see §12's stress case), but nothing here
   requires inventing new machinery for it beyond what "two transitions
   with identical or overlapping bounds" already produces naturally under
   Architecture 1/2's date-based filtering.

**The non-negotiable principle across all seven:** UNKNOWN must remain
UNKNOWN. Every one of the three architectures satisfies this for
Architecture 1/2 by construction (a down-set/tuple with no evidence either
way is generated as a *candidate*, never silently collapsed to one answer);
Architecture 3 satisfies it only when the author remembers to write the
competing states, which §3.H (YZ-Tank Dragon) shows even this project's own
past authoring did not reliably do.

---

## 6. Transition-centric vs. state-centric: is either primary?

**Transition-centric** (Architectures 1 and 2): store the changes and the
evidence relating them; derive the state space and its candidates at query
time. **State-centric** (Architecture 3): store the meaningful historical
states directly, with their own plausibility evidence; transitions are not
stored, only implied by adjacent states.

The task frames this as a real tension, and it is one — but the tension is
resolved differently for the two halves of the problem the model has to
solve:

- **For chronology** (which states are plausible at a snapshot),
  transition-centric wins clearly. The evidence this project actually has
  — dates, bounds, "cannot be sequenced" statements — is evidence *about
  transitions*, not about states directly; period sources describe "when
  did the ruling change," not "here is the complete list of ways this card
  behaved and when each applied." Forcing that evidence into a
  state-centric shape (Architecture 3) means re-deriving state predicates
  from transition evidence by hand every time, which §3.F (Necrovalley)
  shows is strictly more work than deriving it mechanically, and §3.H
  (YZ-Tank Dragon) shows is a place this project's own authoring has
  already gotten wrong once.

- **For implementation mapping** (what EDOPro artifact reproduces a given
  state), state-centric wins clearly, for the reason §1 and §4 already
  established: a script *implements a state*, not a transition. Attaching
  implementation data to a transition (today's `resulting_implementation`)
  is exactly the design error this whole document exists to correct.

**Recommendation: a hybrid, not a compromise.** Store transitions and their
order relation (transition-centric) for chronology; store implementation
coverage keyed explicitly by state (state-centric) for the EDOPro mapping.
This is precisely Architecture 1 (and, isomorphically, Architecture 2) as
already specified in §2 — the "hybrid" is not a fourth architecture, it is
the recognition that Architectures 1/2 already *are* the hybrid, and
Architecture 3's attempt to be state-centric for *both* halves of the
problem is what makes it strictly worse at the chronology half without
being any better at the implementation half (which Architectures 1/2
already handle by explicit state-keying, without needing to give up the
transition-centric chronology derivation).

---

## 7. Migration analysis

The 296-record corpus, mechanically split first by relevant-change count
(`kind in {functional, ruling}`, matching today's
`IMPLEMENTATION_RELEVANT_KINDS`):

| Relevant changes | Records | % of corpus |
|---|---|---|
| 0 or 1 | **236** | 79.7% |
| 2 | 56 | 18.9% |
| 3 | 2 | 0.7% |
| 4 | 2 | 0.7% |
| **2+ total** | **60** | **20.3%** |

The 236 are trivially "one transition, two states" or "zero
implementation-relevant transitions" under any of the three architectures
(§3.G) — no ordering question exists for them, and migrating them is a
mechanical rename regardless of which architecture is chosen.

The 60 with 2+ relevant changes were classified into the four categories
this document has used throughout, using **two independently-sourced
passes, cross-checked against each other**: this project's own exhaustive,
adversarially-verified Edison audit (commits 25cd7f4 → c913817, covering
the 44 records already known to matter for the Edison format) for
already-known records, and a fresh batched classification workflow (10
agents, 6 records each) for everything else, run against the same
evidence-based criteria established in that audit (do not treat `changes[]`
list order as evidence; "bundled" requires substantive same-ruling
language, not just an undated pair).

**Cross-validation result:** the fresh workflow reproduced the Edison
audit's own classification for 40 of the 44 already-known records exactly,
and disagreed on 4 (Bubonic Vermin, Dark Mimic LV1, Skull Knight #2 — each
misclassified as `mechanically-distinct-order-unknown` when direct
re-reading of their review notes confirms the same "no upstream
implementation exists for the intermediate state" bundling language present
in the other 35 correctly-classified cluster-1 records; and Paladin of
White Dragon, conservatively flagged `needs-manual-review` rather than
`bundled-independent-axis`, which is a reasonable caution given its
three-transition, mixed-relationship structure rather than an outright
error). The Edison audit's own classification is used for all 44 in the
totals below, since it was independently adversarially verified three times
already; the fresh workflow's ~91% raw agreement rate on records it did not
know the answer to in advance is treated as moderate, not full, confidence
in its classification of the genuinely new 16 — each of which is named
explicitly below rather than folded into an unlabelled total.

| Category | Records | Notes |
|---|---|---|
| Trivial (0-1 relevant changes) | **236** | mechanical rename, any architecture |
| Fully-ordered multi-transition | **13** (new) + **5** already known as B-partition chains (Blackwing - Sirocco the Dawn, Dark Necrofear, Necrovalley, Night Assailant, Soul Rope — counted once, inside the 13) | verified directly: every relevant change in all 13 carries real dating info, zero exceptions |
| Bundled/independent-axis | **38** (Edison cluster-1) + **1** new (YZ-Tank Dragon — *both* changes undated, a strictly harder shape than any Edison case, §3.H) = **39** | needs explicit axis/edge annotation on migration |
| Mechanically-distinct, order-unknown | **6** (Edison non-cluster) | needs explicit "unknown" annotation, no bundling label |
| Needs manual review | **2** (Insect Imitation, Last Will — researcher-asserted, undated order claim, §3.I; no clean precedent for this shape) | flagged, not force-classified |
| **Total** | **296** | 236 + 13 + 39 + 6 + 2 = 296 |

**Do not trust the Edison 44/85 as the entire affected population** — the
task's own instruction, and correct: 16 records outside Edison's
known-wrong/divergence set have 2+ relevant changes, of which 3 (YZ-Tank
Dragon plus the 2 needs-manual-review records) are not simple dated chains.
None of these 3 currently produce a *visible* symptom, precisely because
(per §3.D's later-snapshot finding) the self-contradictory-candidate defect
is snapshot-dependent — a record can look fine today and misbehave only
once a future, not-yet-defined format queries it at the wrong date. This is
the concrete argument for doing this redesign *before*, not incidentally
during, the chronological-reconstruction work the project intends next:
every new format is a new chance to discover one of these 3 (or an
as-yet-unaudited record among the 236 "trivial" ones, if a future erratum
addition turns a currently-single-transition record into a multi-transition
one) the hard way, at build-break time on an unrelated task, rather than
during a scoped audit like this one.

**What "needs manual review" should mean going forward:** not "blocked
indefinitely," but "requires a human to decide, once, which constraint tier
in §5 applies (§5.3 evidenced order, §5.4 explicit unknown, or §5.6
researcher-inference) before the record can be mechanically migrated" — a
small, bounded task for exactly 2 records today, not a scaling concern.

---

## 8. Backwards compatibility

Four options, as posed by the task:

- **(A) Replace the schema outright.** Fastest to reach a clean end state;
  highest short-term risk (every record touched in one migration, no
  ability to land it incrementally, no fallback if a subtle behaviour
  change is discovered mid-migration).
- **(B) Introduce schema v2 and migrate.** A defined cutover: v1 stops
  being accepted after migration completes. Lower risk than (A) if the
  migration itself is staged (e.g. migrate the 236 trivial records first,
  as a mechanical, low-risk commit, before touching the 60 harder ones).
- **(C) Support old and new forms temporarily.** Both schemas valid,
  `Repository.load()` dispatches per-record on shape. Highest ongoing
  complexity (two code paths through `model.py`/`validate.py` for the
  duration), justified only if the migration must be spread across many
  independent commits over a long period with the repository staying
  fully functional throughout.
- **(D) Normalise both forms internally into one state model.** Parse
  either v1 or v2 JSON shape into the *same* in-memory `Erratum`
  representation (the down-set/state structure from Architecture 1),
  computed from v1 records via the existing chain-inference (which is
  already correct for the 236+13 records that are genuinely simple or
  fully dated) and read directly for v2 records.

**Recommendation: (D) as the transitional mechanism, converging to (B) as
the end state — not (C).** The task's own framing is decisive here: "we
are early enough that compatibility with our own obsolete schema is not
inherently valuable... prefer conceptual cleanliness... [but] deterministic
generated output and existing verified behaviour must not silently drift."
(D) satisfies both halves of that sentence at once: it lets `model.py`
have exactly *one* internal representation and exactly *one* selection
algorithm (conceptual cleanliness — no permanent dual code path, unlike
(C)), while letting the 236+13 = 249 records that are already
unambiguously simple stay in their current JSON shape until someone
chooses to touch them (no forced, deterministic-output-risking rewrite of
records nobody has reason to revisit), with a real, testable equivalence
proof (a v1 record and its migrated v2 equivalent must select identically
at every currently-defined format snapshot — a mechanical regression test,
not a one-time manual check) gating any actual migration commit. Once every
record has been touched (driven by whichever future task needs to touch
it, not a forced big-bang), v1 parsing can be deleted and (D) becomes a
plain (B).

This explicitly rejects (C) as a *permanent* state: temporary dual-shape
support during migration is just (D)'s normalisation layer described
differently, but (C) as the task poses it — the schema itself permanently
accepting either shape — would mean `schemas/erratum.schema.json` forever
carrying two incompatible `changes`-vs-`transitions` property sets, which
is exactly the kind of "preserving a bad abstraction to avoid migration
work" the task explicitly says not to do.

---

## 9. Selection API design

Today's `ErratumSelection` (`retroformats/model.py:213-255`) exposes
`state`, `implementation`, `version_index`, `ambiguous_changes`,
`candidates` (a tuple of **integers**), and `modern_version` (an
**integer**). The redesign replaces every integer with a reference to a
named, semantic state — nothing in the new public API should require the
caller to know how many transitions preceded a given position, only what
state it is.

```python
@dataclass(frozen=True)
class HistoricalState:
    key: frozenset[str]              # transition ids applied in this state, e.g. frozenset({"activation-semantics"})
    label: str                       # human-readable, generated: "verification=old, activation-semantics=new"
    implementation: dict | None      # None only for a state the validator has already rejected as unreachable

@dataclass(frozen=True)
class ErratumSelection:
    outcome: str                     # "determinate" | "ambiguous" | "gap" | "modern"
    candidates: tuple[HistoricalState, ...]   # always the full plausible set; len == 1 iff determinate
    modern_state: HistoricalState             # the terminal state, for "is modern among candidates" checks
    ambiguous_transitions: tuple[str, ...]    # transition ids (not positions) whose own state was AMBIGUOUS at this snapshot
```

`outcome` folds today's four-way `state` field into one string, but note
what changed: `"historical"` becomes `"determinate"` with
`candidates[0].implementation` carrying a non-modern implementation — the
caller no longer needs a separate `version_index == 0` check
(§10 keeps this comparison available as `candidates[0].key == frozenset()`,
still supported, just no longer numeric-position-dependent) to ask "is this
the baseline."

Example returned structures for the five cases the task asks for:

```python
# Determinate modern (e.g. a snapshot after every transition's date)
ErratumSelection(
    outcome="modern",
    candidates=(HistoricalState(key=frozenset({"axis1", "axis2"}), label="modern", implementation=None),),
    modern_state=HistoricalState(key=frozenset({"axis1", "axis2"}), label="modern", implementation=None),
    ambiguous_transitions=(),
)

# Determinate historical (e.g. Necrovalley at a snapshot between two of its four dates)
ErratumSelection(
    outcome="determinate",
    candidates=(HistoricalState(key=frozenset({"v1-scope"}), label="v1 negation scope",
                                 implementation={"strategy": "reuse-upstream", "historical_passcode": ...}),),
    modern_state=HistoricalState(key=frozenset({"v1-scope", "v2-scope", "v3-scope", "v4-scope"}), label="modern", implementation=None),
    ambiguous_transitions=(),
)

# Ambiguous two-state (Giant Rat at Edison)
ErratumSelection(
    outcome="ambiguous",
    candidates=(
        HistoricalState(key=frozenset(), label="both old (baseline)",
                         implementation={"strategy": "reuse-upstream", "historical_passcode": 504700172}),
        HistoricalState(key=frozenset({"activation-semantics"}), label="verification=old, activation=new",
                         implementation={"strategy": "unresolved", "gap": {...}}),
    ),
    modern_state=HistoricalState(key=frozenset({"verification", "activation-semantics"}), label="modern", implementation=None),
    ambiguous_transitions=("activation-semantics",),
)

# Known implementation gap (determinate chronology, missing implementation)
ErratumSelection(
    outcome="gap",
    candidates=(HistoricalState(key=frozenset({"activation-semantics"}), label="verification=old, activation=new",
                                 implementation={"strategy": "unresolved", "gap": {"reason": "..."}}),),
    modern_state=HistoricalState(key=frozenset({"verification", "activation-semantics"}), label="modern", implementation=None),
    ambiguous_transitions=(),
)

# Multi-axis ambiguity (Paladin at a hypothetical snapshot where all three transitions are ambiguous)
ErratumSelection(
    outcome="ambiguous",
    candidates=(  # up to 8 HistoricalState entries, one per surviving down-set
        HistoricalState(key=frozenset(), label="all old", implementation={...}),
        HistoricalState(key=frozenset({"activation"}), label="activation=new only", implementation=None),
        HistoricalState(key=frozenset({"attack-restriction"}), label="attack-restriction=new only", implementation=None),
        # ... up to 5 more, filtered by whatever per-transition states are actually AMBIGUOUS at this snapshot
    ),
    modern_state=HistoricalState(key=frozenset({"activation", "verification", "attack-restriction"}), label="modern", implementation=None),
    ambiguous_transitions=("activation", "verification", "attack-restriction"),
)
```

`modern_is_possible` and `acknowledged_gap` (today's two computed
properties) survive unchanged in spirit: `modern_state in candidates` and
`candidates[0].implementation.get("gap")` respectively — both now readable
without touching an integer.

---

## 10. Validation design

Invariants the validator must enforce, extending today's
`_validate_errata` (`retroformats/validate.py:274-...`) rather than
replacing its intent:

1. **Every `after` / axis-order reference names a transition or axis that
   exists** in the same record — today has no equivalent (there is nothing
   to reference), this is new.
2. **No dependency cycles** in the `after` relation — a transition cannot
   (transitively) require itself. Detectable at parse time by a standard
   topological sort; reject the record if one fails.
3. **Every entry in `states[]` is a valid down-set** of the `after`
   relation (or a valid axis-position tuple) — an author cannot claim an
   implementation for a combinatorially unreachable state (e.g. a state
   requiring transition B without transition A, when B's `after` names A).
4. **No duplicate state keys** — two `states[]` entries cannot claim the
   same down-set/tuple.
5. **The all-transitions-applied state is unambiguously `"modern"`**, and
   no other state may be — generalises today's
   `erratum.modern-implementation-recorded` check (which currently only
   guards the *last list entry*) to the true terminal state of the DAG,
   which for a non-chain record is not simply "the last array entry."
6. **Contradictory chronology constraints are rejected** — generalises
   today's `erratum.changes-out-of-order` check (`retroformats/
   validate.py:285-309`) from "the whole flat list" to "each declared
   `after` edge specifically": if transition B declares `after: [A]` but
   B's `new_attested_from` (or exact date) predates A's
   `old_attested_through` (or exact date), that is a definite,
   structural contradiction between the declared order and the dated
   evidence, and must be a hard error, not a warning.
7. **Exact/bounded dates and the declared partial order must agree** — the
   inverse direction of (6): if two transitions have *no* declared `after`
   edge between them, but their dates make one's order relative to the
   other unambiguous (e.g. both are exactly dated, with no overlap), the
   validator should at minimum warn that an explicit `after` edge would be
   more informative than relying on inferred-from-dates order — not an
   error (dates alone are sufficient evidence), but a lint-level nudge
   toward the more auditable form.
8. **Unreachable state mappings are detected** — a `states[]` entry whose
   down-set can never be a candidate at *any* possible snapshot (e.g. it
   requires a transition whose own dating structurally excludes it from
   ever coexisting with another required transition in that same state) is
   flagged — dead data, most likely an authoring mistake.
9. **Ambiguity cannot silently fall back unless policy explicitly allows
   it** — unchanged in principle from today's
   `format.erratum-ambiguous`/`unresolved_policy` handling
   (`retroformats/validate.py:805-843`), just operating over the new
   `ErratumSelection.candidates` tuple of states instead of integers.
10. **The Edison-audit heuristic, formalised**: an undated transition whose
    *default* `after` (chain-to-previous-entry, when not explicitly
    overridden) would connect it to a transition dated far enough away
    that review-note text nearby uses language matching `/cannot.{0,20}be
    sequenced|order.{0,20}(is |remains )?unknown/i` (the exact phrasing
    found, independently worded, in every one of the 44 Edison C-partition
    records) triggers a validator **warning**, not error, prompting a human
    to confirm whether `after: []` was intended. This is a lint, not a
    hard gate, because false positives are expected and acceptable — its
    job is to have caught what this project's own past authoring missed
    (§3.H), not to block every legitimately-chained record whose review
    notes happen to discuss uncertainty in nearby, unrelated prose.

---

## 11. Build impact (traced, not modified)

| File | What would change |
|---|---|
| `schemas/erratum.schema.json` | New `transitions[]` (replaces `changes[]`), new `states[]` (replaces `implementation` + per-change `resulting_implementation`), new `$defs` for a down-set/state key type; `changes[]` retained during the (D) transition period (§8) for records not yet migrated. |
| `retroformats/model.py` | `Erratum.relevant_changes()`/`implementation_for_version()`/`selection_at()` replaced by down-set enumeration + state lookup (§2 Architecture 1, §9's `ErratumSelection`); `change_state_at()` is reused almost unchanged — it already correctly computes one transition's OLD/AMBIGUOUS/NEW, which is exactly the primitive the new algorithm composes over many transitions instead of assuming a chain. |
| `retroformats/validate.py` | `_validate_errata`'s ordering check (lines 285-309) generalised per §10.6; every `selection.version_index`/`selection.candidates` (integer) consumer (lines 743, 781, 789, 801, 810, 821-822, 839, 853, 862 — traced in the current-implementation review for this document) becomes a `HistoricalState` consumer; the `format.erratum-include-wrong-version`/`-redundant` checks (789-803) become key-equality checks (`candidates[0].key == frozenset()`) instead of `== 0`. |
| `retroformats/lflist.py` | `select_applicable_errata()` (lines 200-259) and `baseline_override()`/`parity_override()` (lines 145-180) already operate mostly on `selection.state`/`.implementation` directly, not on integers — the smallest-touched file of the four; `parity_override()`'s "walk the chain in order, take the first usable implementation" logic (§ current code review) needs a defined replacement policy for a non-chain record (recommendation: walk states in a canonical order — fewest transitions applied first, ties broken by transition id — which degenerates to today's exact behaviour for every genuine chain). |
| Importers | None currently generate multi-transition records automatically (confirmed: `imported`-status records are single-implementation stubs) — no importer changes expected, but the `imported`/`reviewed` review-status gate (unchanged concept) still applies. |
| Report output (`retroformats/cli.py` `report -v`) | Cosmetic only — wherever it prints `version {selection.version_index}` today, it would print `state {label}` instead; no structural change. |
| Tests | `tests/test_errata.py::OrderingConstraintTest` and `tests/test_repo_data.py::test_giant_rat_selection_shape` (added by the Edison audit specifically to characterise *current*, not-yet-fixed behaviour) must be rewritten against the new semantics, not merely kept passing — they exist to pin down the bug, and the redesign's entire purpose is to no longer have that bug. |
| Existing JSON records | Per §7/§8: 249 records (236 trivial + 13 fully-ordered) migrate mechanically; 39 bundled + 6 order-unknown + 2 manual-review = 47 records need a human to add explicit `after`/axis-order annotations. |
| Generated `dist/` output | Must not change for any currently-defined format at all — this is the regression gate §8 already specifies (v1-vs-migrated-v2 equivalence at every current snapshot), not a change this redesign is expected to cause.

---

## 12. Adversarial review

Each stress case, against all three architectures, plus the deliberately
smaller "something simpler" idea deferred from §2.

**1. Three independent binary axes.** Architectures 1/2: 2³ = 8 down-sets
/ tuples, mechanically generated, no special handling needed — this is the
same machinery as Giant Rat's 2-axis case, one dimension larger.
Architecture 3: an author must recognise and author up to 8 states by
hand; nothing currently in the corpus has this shape (max observed is 2
independent axes, or Paladin's 2-bundled-plus-1-separate), but nothing
structurally prevents a future card's history from taking this shape, and
Architecture 3 is where it would first become genuinely error-prone rather
than merely more verbose.

**2. Partial ordering: A < C, B unordered relative to both.** The
sharpest test of whether an architecture is a true partial order or
secretly still a chain-plus-flag. Architecture 1: native — `C.after =
[A]`, `B.after = []`; down-set enumeration automatically respects "any
down-set containing C also contains A" while leaving B free. Architecture
2: expressible but indirect — either A and C are declared on the same axis
(trivial, their order is just the axis's own internal order) or on
different axes with one `axis_order` entry constraining the A/C pair and
none constraining B, which works but requires the author to reason in
terms of cross-axis position pairs rather than a direct edge on the
transition itself. Architecture 3: fully manual — the author must encode
"plausible only if A's date/evidence holds and C has not yet occurred
without A" directly into `plausible_when` predicates for every affected
state, with no structural check that the encoding is self-consistent. **A
two-valued `order: "chained" | "independent"` field on each change — the
smaller alternative floated in the Edison audit and explicitly retracted
there — fails this case outright**: a boolean cannot distinguish "unordered
relative to A specifically" from "unordered relative to everything," so it
cannot express A<C-but-B-free at all. No record in today's corpus happens
to need exactly this shape yet (every multi-axis record found is either
fully chained or fully unordered pairwise), but nothing rules out a future
card whose history combines a bundled pair with one separately-ordered
addition — structurally one step short of what Paladin already has today
(three transitions, order only *partially* absent), which is why this
document treats it as a real requirement, not a hypothetical one.

**3. Two transitions whose order becomes known later.** Not a structural
stress test for any of the three — an ordinary edit (add the now-known
`after` edge / `axis_order` entry / rewrite the affected
`plausible_when`), re-validate. Architectures 1/2 benefit here specifically
because the candidate *state count* shrinks automatically and
provably-unreachable `states[]` entries become detectable by §10.8's
invariant, prompting cleanup; Architecture 3 requires the author to notice
and manually retire now-stale states, with no structural signal that one
has gone stale.

**4. Multiple transitions on the same behavioural axis.** The ordinary
case, not a stress test — this is what "axis" *means* in §1's definition,
and Necrovalley (§3.F, four transitions on presumably-related dimensions)
already exercises it without incident under any architecture.

**5. State implementations missing for only some, non-contiguous
combinations.** Giant Rat (§3.A) already exercises the two-of-four case.
Architectures 1/2 scale this cleanly to larger spaces — author whichever
`states[]` entries need an implementation, everything else defaults per
§10's documented policy. **This is where Architecture 3 shows its sharpest
weakness**: because it has no down-set enumeration to check completeness
against, it cannot distinguish "this state was considered and confirmed to
have no implementation" from "this state was never considered at all" —
both look identical (absence of an entry). Architectures 1/2 can represent
this distinction explicitly (an authored `states[]` entry with
`implementation: null` plus an `unresolved: true`/gap marker, vs. no entry
at all defaulting per policy); Architecture 3 would need an equivalent
explicit placeholder convention bolted on to recover the same guarantee,
at which point it is no longer meaningfully "simpler" than the others for
this exact situation.

**6. Two transitions on the same exact date.** Not a real stress case:
`change_state_at`'s existing day-precision boundary semantics (inclusive
on the effective date) already give both transitions the identical
OLD/NEW state at every snapshot, under all three architectures, whether or
not an `after` edge is declared between them — an explicit edge is
optional documentation, not required for correctness here. §10.7's lint
(suggesting an explicit edge when dates already disambiguate order) does
not fire for same-date transitions specifically, since dates do *not*
disambiguate their relative order in this case — correctly left unordered.

**7. Cosmetic changes interspersed with behavioural ones.** Unaffected by
architecture choice — `kind in {functional, ruling}` filtering
(`IMPLEMENTATION_RELEVANT_KINDS`) happens *before* any transition ever
enters the DAG/axis/state machinery, identically to today's
`relevant_changes()`. Verified already working correctly today (test:
`test_mixed_kinds_only_relevant_changes_count`) and this document proposes
no change to that filter.

**8. An engine-level behaviour rather than a card-script behaviour.**
Explicitly out of scope, and this document does not attempt to unify the
two systems. `kind: "engine"` transitions are excluded from
`IMPLEMENTATION_RELEVANT_KINDS` today because engine-era behaviour is
governed by rule profiles (format-level `DUEL_*` flag sets,
`docs/research/edison-rules.md` territory), not per-card overrides, and
that separation is a different, structurally distinct problem this
redesign does not touch. Flagged here as a noted-but-deferred question —
if a future audit finds rule-profile-level ordering ambiguities of the
same shape (this project's roadmap already tracks at least one candidate,
the SEGOC-ordering-versus-Ignition-Priority open item), it would need its
own, separately-scoped design, not an extension of this one.

**9. Future chronological formats querying dates far outside GOAT/
Edison.** The motivating case for the entire document, already worked
through concretely in §3.D: Tyrant Dragon evaluated at 2014-01-01 (a date
no currently-defined format queries) reproduces, under *today's* schema,
the identical self-contradictory-candidate defect Giant Rat already shows
at Edison — proving the defect is not Edison-specific, only
Edison-*undiscovered* so far. Every one of the three redesigned
architectures gives the snapshot-independent-correct answer at that same
2014 date (§3.D's table), which today's schema-plus-list-order cannot
claim at any snapshot for any of the 44+1 currently-known-affected
records.

**Where does state-space explosion become a real concern?** Nowhere at
this project's actual scale. The corpus scan (§7) found a maximum of 4
relevant transitions on any real record, and only 2 records reach even
that; 2⁴ = 16 states is the realistic worst case today. A deliberately
generous upper bound — 10 relevant transitions on one card, roughly triple
the highest count ever observed, allowing for decades of future
chronological-reconstruction work adding more eras — gives 2¹⁰ = 1024
states, still trivial to enumerate in microseconds during `validate`/
`build`. Explosion would only become a real concern if the transition
filter (§12.7) were removed (letting cosmetic churn into the DAG) or if a
record's behavioural history were genuinely dozens of independent axes
deep, which nothing in twenty-plus years of Yu-Gi-Oh! ruling history for
any single card comes close to. This is not a design constraint worth
optimising against; it is a design constraint worth *stating*, explicitly,
so a future reviewer does not need to re-derive it from scratch.

---

## 13. Recommendation

**Architecture 1 — transition partial order (DAG) with `after` edges,
plus an explicit per-state implementation map — is the recommended
design.**

**Why more correct than the alternatives.** It is the only one of the
three that derives the *entire* state space and its implementation
coverage mechanically from evidence actually present in the record, with
no reliance on array position (unlike today's schema), no requirement that
an author correctly intuit axis boundaries up front (unlike Architecture
2, where a mis-drawn axis boundary is a silent modelling error the
validator cannot catch), and no reliance on an author's manual
completeness discipline (unlike Architecture 3, which §3.H and §12.5 both
show has already produced a real, first-party admission of exactly the
list-order-as-narrative-convenience failure this document exists to
close). Architecture 2 is a close second on correctness (§12.2 shows it
handles every stress case, just less directly than Architecture 1) and is
revisited below as the authoring-ergonomics layer, not discarded.

**Why simple enough for contributors.** For 249 of 296 records (§7: 236
trivial + 13 fully-ordered), Architecture 1's default (`after` implicitly
chains to the previous list entry unless overridden) makes migration a
rename with no new concept to learn — a contributor authoring an ordinary,
single-evolving-question erratum record, which is the overwhelming
majority case, never needs to write `after` at all. The added vocabulary
(`after: []`, `states[]` keyed by applied-transition-sets) is used only by
the 47 records that already needed a human to think carefully about
ordering — the complexity is proportional to the genuine complexity of the
record, not a tax on every author for every record. **Ergonomic
refinement adopted from Architecture 2:** when a record's transitions form
one connected, unordered-relative-to-nothing-else axis (i.e. the DAG *is*
a single chain), the schema should permit an optional `axes[]`-style
sugar — grouping transitions under a named axis label purely for
readability — that desugars to identical `after` edges underneath. This
costs nothing structurally (it is sugar, not a second mechanism) and
recovers Architecture 2's clearest advantage (a reader immediately sees
"this record has 2 independent questions" from the shape of the JSON) at
authoring time, without adopting axis as a second computational primitive
the way a pure Architecture 2 would.

**Migration strategy.** Per §8: normalise-both-forms internally (option
D), converging to schema-v2-only (option B) once every record has been
touched, gated at every step by the v1-vs-migrated-v2 selection-equivalence
regression test at every currently-defined format snapshot. Staged by §7's
categories, cheapest and lowest-risk first: 236 trivial records, then 13
fully-ordered, then the 47 records needing explicit annotation (39 bundled
+ 6 order-unknown + 2 manual-review), each stage independently
committable and independently regression-gated.

**Selection algorithm.** §2's down-set enumeration over `after`, filtered
per snapshot by `change_state_at()` (reused, not replaced) applied to each
transition individually — §9's `ErratumSelection`/`HistoricalState`
replacing today's integer-indexed fields.

**Implementation mapping strategy.** §4: `states[]` keyed by
frozenset-of-applied-transition-ids, not by chain position; the six
implementation kinds (§4's table) attach identically to a state regardless
of how many transitions produced it.

**Validator strategy.** §10's ten invariants, of which (2) cycle detection,
(3)/(4) down-set validity and uniqueness, and (10) the Edison-audit-derived
"cannot be sequenced" lint are new; (6)/(9) are direct generalisations of
today's `erratum.changes-out-of-order` and ambiguity-fallback checks.

**Expected files touched by the eventual implementation** (traced in §11,
not modified in this milestone): `schemas/erratum.schema.json`,
`retroformats/model.py`, `retroformats/validate.py`, `retroformats/
lflist.py` (smallest touch of the three code files), `tests/test_errata.py`
and `tests/test_repo_data.py` (rewritten against corrected semantics, not
merely kept passing), and the 47 records identified in §7 as needing
explicit human annotation.

### Proposed atomic implementation sequence (for the future milestone — not this one)

1. **Schema v2 alongside v1.** Add `transitions[]`/`states[]`/`after` to
   `schemas/erratum.schema.json` as an alternative to `changes[]`, valid
   but unused by any record yet. No `model.py` changes. Pure schema
   addition, independently reviewable.
2. **Dual-shape parsing, single internal representation.** `Erratum.load()`
   detects which shape a record uses and normalises both into the
   down-set/state internal structure (§8 option D). New
   `selection_at()`/`ErratumSelection`/`HistoricalState` implemented
   against the internal structure only. Old integer-based
   `ErratumSelection` fields kept as deprecated compatibility shims
   (computed from the new structure) so `validate.py`/`lflist.py` do not
   need to change in this commit. Gated by the v1-vs-v2 equivalence test
   (new) run against every existing record parsed both ways where
   applicable (trivially, since no record uses v2 shape yet, this
   commit's own test is "every v1 record round-trips through the new
   internal structure to the same selection as the old algorithm, at
   every defined snapshot").
3. **Migrate the 236 trivial + 13 fully-ordered records.** Mechanical,
   scripted transform (`changes[]` → `transitions[]` with implicit
   `after`-chains, `implementation`/`resulting_implementation` →
   `states[]`). Regression-gated by the same equivalence test. No manual
   review needed per §7's classification.
4. **Migrate the 6 mechanically-distinct/order-unknown + 39
   bundled/independent-axis records**, `after: []` applied per the
   already-published Edison audit's exact classification (no new research
   needed — this work is already done and committed). Regression-gated;
   this commit is expected to *change* the computed candidate set for the
   29-of-38 records already known to be self-contradictory today (that is
   the fix landing), verified against the already-published corrected
   `docs/research/edison-behaviour-gaps.md` expectations.
5. **Resolve the 2 needs-manual-review records** (Insect Imitation, Last
   Will) — a human decision on which §5 constraint tier applies, informed
   by §3.I's analysis, then migrated per whichever tier is chosen.
6. **Switch `validate.py`/`lflist.py` to the new `HistoricalState`-based
   API directly**, remove the deprecated integer-based compatibility
   shims from step 2. This is the only commit expected to touch
   `retroformats/validate.py`'s and `retroformats/lflist.py`'s actual
   selection-consuming logic (traced fully in §11).
7. **Delete v1 schema support.** Remove `changes[]` parsing from
   `Erratum.load()`, make `transitions[]`/`states[]` the only valid shape
   in `schemas/erratum.schema.json`. This is the point at which option
   (D) formally becomes option (B) — schema v2 only, per §8.
8. **Retire/rewrite the Edison-audit characterisation tests.**
   `OrderingConstraintTest` and `test_giant_rat_selection_shape`, which
   exist specifically to pin down *current, known-buggy* behaviour, are
   replaced with tests asserting the *correct* semantics the redesign now
   provides (no self-contradictory candidates at any snapshot, for any of
   the previously-affected records).

Each step above is independently committable, independently testable, and
— except for step 4, whose whole point is to change behaviour for the
already-documented 29-of-38 self-contradictory records — independently
verifiable as a no-op against every currently-defined format's generated
`dist/` output.
