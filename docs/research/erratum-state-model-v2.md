# Erratum state-model v2 — architecture research (roadmap item 5c follow-on)

**Scope: design only.** No canonical `data/errata/*.json` record changes, no
`retroformats/model.py`/`retroformats/validate.py`/`retroformats/lflist.py`
changes, no generated `dist/` changes, no schema changes committed in this
milestone. This document exists to choose an architecture and prove it
against real records before any implementation work is scheduled.

**Revision note.** This is a correction of the first version of this
document (commit bb2c6a7), not a new design. Adversarial review found four
architecture-level problems in that version, all fixed here: (1) the
proposed schema let an omitted ordering annotation default to "chained to
the previous array entry" — reintroducing, inside the very schema meant to
eliminate it, the exact array-order-as-evidence bug this research exists to
close; (2) the document had no representation for two transitions known to
have occurred *together*, as one historical event, at an unknown date; (3)
"behavioural axis" was defined as "a maximal chain in the ordering graph,"
which conflates a semantic label (what question a transition answers) with
a graph-structural fact (what order is evidenced) — a real, demonstrable
error, not a stylistic one; (4) the proposed `HistoricalState.implementation`
field mixed an untyped `dict | None` with an informal `"modern"` string
literal in different examples, with no single explicit representation of
the six implementation kinds. Fixing these four, and re-running the
migration analysis with a stricter, fully mechanical test rather than "does
every transition have some dating information," **found four more corpus
records with the same defect this document exists to fix** (`Sangan`,
`Witch of the Black Forest`, in addition to `Insect Imitation`/`Last Will`,
already flagged as borderline) — bringing the total known-affected count
from 44 to 48. All corrections are integrated below; §13's core
recommendation (transition-centric chronology + state-centric implementation
coverage) is unchanged, refined into what this revision calls the
**historical-event DAG**.

**Why now.** `docs/research/edison-behaviour-gaps.md` (commits 25cd7f4,
3e1a63b, c913817) established that the current data model — `changes[]` as a
single linear, ordered, oldest-to-newest chain — is structurally
insufficient for a real, non-trivial slice of the corpus. This document's
own corpus-wide, fully mechanical re-audit (§7) now puts a precise number on
it: **48 of 296 records** produce a self-contradictory candidate label at
*some* snapshot — some already, at the one snapshot this project currently
queries (Edison, 2010-04-24); the rest only at snapshots this project has
not yet queried, which is exactly the risk of building formats
chronologically forward on top of an uncorrected model. Paladin of White
Dragon has three relevant transitions spanning multiple relationship types
in one record, and one corpus record (YZ-Tank Dragon) has *both* of its
transitions completely undated with its own review notes admitting the
existing `changes[]` order was chosen "for continuity," not evidence —
proof that this project's own past authoring has already, at least once,
treated array position as if it carried historical meaning it does not
have.

---

## 1. Domain model, before any schema

### Definitions

- **Historical event.** Something that is understood to have happened once,
  at one point in the card's real-world history (exactly dated, bounded, or
  completely unknown), and that caused one or more behavioural transitions
  simultaneously. This is the corrected primitive of this document (see
  the revision note above and §2's Architecture 1 rewrite) — the first
  version of this document made *transitions* the primitive and treated
  "did these two things happen together" as an afterthought; this version
  makes that question answerable by construction, because co-occurrence is
  now just "two transitions belonging to the same event," not a bolted-on
  special case.

- **Behavioural transition.** One documented change from one card
  behaviour to another, belonging to exactly one event. A transition has a
  *kind* (functional / cosmetic / ruling / engine — only functional and
  ruling are implementation-relevant, matching today's
  `IMPLEMENTATION_RELEVANT_KINDS`) and a description of what changed. It
  does **not** carry its own chronology — the event it belongs to does
  (see below; this is a deliberate simplification over the first version
  of this document, which gave transitions their own `effective` block and
  had to reconcile that with co-occurrence after the fact).

- **Behavioural axis — corrected definition.** A *semantic* label: the
  name of a question or dimension of a card's behaviour that a transition
  answers (e.g. "does a search-effect require a valid target to exist
  before activation," "how does Necrovalley scope its negation"). Axis
  membership is a property an author assigns to a transition directly,
  independent of the ordering graph. **Two transitions may share an axis
  without any chronological relationship being implied by that sharing**,
  and two transitions with a real chronological relationship (one known to
  precede the other) do not thereby become "the same axis" — the earlier
  version of this document's definition ("a maximal totally-ordered chain")
  was wrong precisely because it inferred the semantic fact from the graph
  fact. Concretely: if axis A has transitions A1→A2 (evidenced order) and
  axis B has a single transition B1, and separate evidence shows B1
  preceded A2, the ordering graph legitimately contains an edge from B1 to
  A2 — but B1 does not thereby become "part of axis A." Axis remains
  optional, non-computational, documentation-and-labelling metadata; see
  §2 and §6 for why no candidate architecture should derive it from graph
  structure.

- **Historical state.** A complete, self-consistent assignment of
  occurred/not-occurred to *every* event simultaneously — a full
  description of one way the card could have behaved in play at some point
  in history. The baseline state (no events occurred) and the modern state
  (every event occurred) are always states; every other combination
  reachable under the known ordering and co-occurrence constraints is also
  a state.

- **Constraint between events.** Evidence relating the possible timing of
  two events, either to each other or to absolute dates. See §5 for the
  full, corrected taxonomy — it now has seven kinds, not the five
  originally listed, expanded specifically to cover co-occurrence and
  researcher-inference.

- **Known-before / known-after relationship.** A specific, *always
  explicit* constraint: evidence establishes that event X occurred
  strictly before event Y. **Never inferred from array or object
  declaration position** — this is the single most important correction in
  this revision (see §2).

- **Unknown relative order.** The absence of a known-before/known-after
  relationship between two events. The corpus's default state for any pair
  of events with no explicit constraint declared between them, and — per
  the corrected rule above — this is now true of *every* pair unless an
  author writes an explicit constraint, not merely every pair the author
  forgot to think about.

- **Co-occurring / atomic events.** Two or more behavioural transitions
  known to have happened together, as a single historical occurrence, at a
  shared (possibly unknown) date. Modelled directly: they are transitions
  of *one* event object, not two events with a same-date-or-equivalence
  constraint layered on top (§2 develops why this is cleaner than the
  alternatives the task asked to be compared).

- **Genuinely independent events.** Events with unknown relative order and
  no reason to think their real-world timing is correlated — the joint
  state space is the full, unconstrained cross product of their
  occurred/not-occurred status. The general case; a fully evidenced chain
  is the special case where every pairwise order happens to be evidenced.

- **Implementation coverage for a historical state.** The mapping from a
  state to what EDOPro artifact reproduces it — now a closed, explicit sum
  type (§4), never an untyped `dict | None`, replacing the ambiguity the
  first version of this document was rightly criticised for.

- **Ambiguity at a format snapshot.** More than one historical state is
  consistent with the evidence at a given snapshot date. Not a defect to
  be resolved by guessing.

### Is this a DAG, independent axes, explicit states, a hybrid, or something simpler?

**Answer, corrected: a hybrid — (A) events with an explicit, evidence-only
partial order for chronology, plus (C) explicit state-keyed implementation
coverage for the mapping to EDOPro artifacts, where a "state" is a set of
*events*, not a set of bare transitions. Axis (B) remains a derived,
optional label, not a fourth structure — now correctly derived from
authoring metadata on transitions, never from the ordering graph.**

The reasoning is the same as the first version of this document's, with
one load-bearing addition: chronology and co-occurrence are *both*
questions about events, not about transitions. A period source describes
"this ruling changed" (a transition's content) and, separately, "we know
this happened as part of the same policy revision as that other thing" (an
event-membership fact) or "we don't know when, but we know it happened
before/after that other thing" (an event-ordering fact). Making *events*
the DAG nodes, with transitions nested inside them, lets both of those
evidentiary facts be represented directly, instead of forcing co-occurrence
to be reconstructed after the fact from same-date coincidences (which the
first version of this document could only handle when the shared date
happened to be known and exact — precisely the case the task's evidence
example, "changed in the same policy revision, exact date unknown," rules
out).

---

## 2. Three candidate architectures

Architecture 1 is substantially revised from the first version of this
document (historical-event DAG, replacing the flat transition DAG).
Architecture 2 is revised to reflect the corrected axis definition, which
turns out to remove its main structural advantage (§2's Architecture 2
section explains why). Architecture 3 needed only the sum-type fix (§4) —
it was already state-first and never depended on array order or on
conflating axis with chain structure.

### Architecture 1 — Historical-event DAG + explicit state map (revised)

**Core idea.** The DAG's nodes are **events** (chronological, orderable),
not transitions. Each event carries its own chronology evidence and one or
more behavioural transitions. Ordering between events is **always
explicit** — omitting it means no constraint, never "chained to the
previous entry." Co-occurrence is represented directly: two transitions
that happened together are transitions of the *same* event object, not two
events linked by an equivalence constraint.

**Canonical data shape:**

```jsonc
{
  "id": "erratum-giant-rat",
  "modern_card": { "passcode": 97017120, "name": "Giant Rat" },
  "classification": "ruling",
  "events": {
    "verification": {
      "effective": { "old_attested_through": "2011-02-02", "new_attested_from": "2019-04-03" },
      "transitions": [
        { "kind": "ruling", "axis": "search-reveal-procedure", "summary": "Deck-reveal-on-whiff..." }
      ]
    },
    "activation-semantics": {
      "effective": { "date": null },
      "transitions": [
        { "kind": "ruling", "axis": "search-activation-legality", "summary": "No-valid-target activation allowance..." }
      ]
    }
  },
  "ordering": {},   // no declared constraint between "verification" and "activation-semantics" -- NOT inferred from key order
  "states": [
    { "events": [], "coverage": { "kind": "reuse-upstream", "historical_passcode": 504700172 } },
    { "events": ["activation-semantics"], "coverage": { "kind": "known-gap", "reason": "..." } },
    { "events": ["verification", "activation-semantics"], "coverage": { "kind": "modern" } }
  ]
}
```

Note what changed from the first version of this document: `events` is a
**dict keyed by id**, not an array — object key order carries no meaning
in JSON and this schema must not lean on it even accidentally.
`"ordering": {}` is the explicit, empty statement "nothing is constrained,"
present in the schema rather than merely absent, so a reviewer sees the
absence of order was a *decision*, not an oversight. The
`{ "events": ["verification"], ... }` state (verification alone) is *not*
written here — see §4/§5 for the now-explicit policy on what an
unauthored-but-reachable state means (it is **not** silently "modern," and
it is **not** silently absent from the model — it mechanically defaults to
`{"kind": "unresolved"}`).

**Explicit-order sugar, for the common case:**

```jsonc
"ordering": {
  "chains": [["v1", "v2", "v3", "v4"]],       // sugar for pairwise "v1 before v2 before v3 before v4"
  "edges": [{ "before": "b1", "after": "a2" }] // ad hoc pairwise constraint, for non-chain partial orders
}
```

`chains` is pure sugar over `edges` — `["v1","v2","v3"]` desugars to
`{before: v1, after: v2}` + `{before: v2, after: v3}`, nothing more. There
is **no default chain inferred from `events{}`'s own key order** — a
record with four events and no `ordering` block at all has *zero* declared
edges, full stop, regardless of what order the events happen to be written
in the JSON. This is the direct fix for the defect this whole document
exists to close: **omitted ordering information means no edge, never "the
previous item."**

**Co-occurrence, worked example** (the task's own evidence case:
*"Behaviour A and behaviour B changed in the same Konami policy revision,
but the exact date of that revision is unknown"*):

```jsonc
"events": {
  "policy-revision": {
    "effective": { "date": null, "basis": "Konami policy revision, exact date unresolved" },
    "transitions": [
      { "kind": "ruling", "axis": "axis-a", "summary": "Behaviour A..." },
      { "kind": "ruling", "axis": "axis-b", "summary": "Behaviour B..." }
    ]
  }
}
```

One event, two transitions. There is exactly one occurred/not-occurred
status for the whole event, so the only two states this record's
`events{}` can *ever* produce are `{}` (neither A nor B) and
`{policy-revision}` (both A and B) — **the mixed states (A alone, B alone)
are not merely unauthored, they are not structurally generable at all**,
because down-set enumeration operates over events, and this record has
only one event. This is the direct answer to the requirement that a plain
partial order cannot express this case (no edge between two independent
events gives 4 combinations; `A < B` or `B < A` gives 3; both directions is
an invalid cycle — none of which is "exactly 2, symmetric"): declaring the
two transitions one *event* instead of two ordered/unordered events gives
exactly 2, which is precisely what "known to occur together" evidence
should produce, and — critically — it cannot be produced by accident, because it
requires an author to write one `transitions` array with two entries
instead of two `events` entries. Giant Rat, where no such evidence exists,
naturally stays as two separate one-transition events (§2's canonical
example above) — simultaneity is never the default, only ever an explicit
authoring choice, which directly satisfies the requirement that Giant
Rat's independence must not be accidentally overridden.

**Selection algorithm.** For a snapshot: compute each *event's*
OLD/NEW/AMBIGUOUS state via `change_state_at()`-equivalent logic applied to
the event's own `effective` block (transitions no longer carry one). A
down-set of events is a candidate iff every included event is
NEW-or-AMBIGUOUS, every excluded event is OLD-or-AMBIGUOUS, and the
down-set respects every `ordering` edge. Collect all candidate down-sets;
look each up in `states[]`, defaulting per §4/§5's policy for anything
reachable but unauthored.

**Implementation lookup.** `states[]` keyed by the down-set of *event*
ids — same mechanism as the first version of this document, just correctly
scoped to events instead of bare transitions, which is what makes
co-occurrence representable without a second mechanism.

**Ambiguity representation.** The set of down-sets consistent with the
per-event evidence at the snapshot (§9).

**Validator invariants (preview; full list in §10).** Every `ordering`
reference names a real event id (order-independent of declaration position
— arbitrary forward/backward references are fine, cycle detection does the
real work, not declaration order, per the task's explicit instruction);
`chains`/`edges` together must not contain a cycle; every `states[]` entry
must be a down-set the DAG can actually produce; the all-events state must
map to `coverage.kind == "modern"` and no other state may; §10.6's
corrected, now-mechanical (not merely text-matching) check for
undated/overlapping-bound event pairs with no declared edge, which §7's
re-audit shows finds real, previously-undetected corpus defects, not just
Edison-shaped ones.

**Migration complexity.** Revisited under the corrected, no-implicit-order
rule in §7 — the honest answer is that *no* record migrates as a pure,
zero-thought rename any more, because a migration script must **prove**
each edge it emits, not merely copy list order into it. §7 works through
exactly how that proof is constructed mechanically for the records where it
can be, and precisely which records it cannot be proven for automatically.

**Computational complexity.** Unchanged in kind from the first version of
this document — bounded by 2^(events), realistic worst case still 16 (§7
confirms no record has more than 4 implementation-relevant events even
under this stricter audit).

**Human-authoring ergonomics.** The event/transition split costs one extra
level of nesting for every record (even the simplest), which is real,
non-zero overhead relative to today's flat `changes[]` — but it removes an
entire class of silent authoring error (accidentally implying
co-occurrence or order that isn't evidenced) that the flatter shape could
not represent correctly at all. §13 proposes a concrete mitigation:
single-transition, single-event records (the overwhelming majority) may
elide the nesting via sugar, so the common case does not pay the full
verbosity cost.

**Excluding contradictory/impossible states.** Structurally, by
construction, exactly as the first version of this document argued — the
correction changes *what* a down-set ranges over (events, not bare
transitions) but not the soundness of the argument.

**Scaling 1 → 2 → 3+ events, with and without co-occurrence.** 1 event: 2
states, no `ordering` needed. 2 events, no co-occurrence, no order:
4 down-sets (Giant Rat). 2 transitions, co-occurring: 1 event, 2 down-sets
(the policy-revision example above). 3+ events, mixed relationships:
Paladin (§3.C) — three single-transition events, no declared edges among
any pair (order unevidenced for all three, confirmed by the corrected §7
audit below), 8 combinatorial down-sets, snapshot-filtered to 2 surviving
candidates at Edison, matching the live, already-committed selection
output.

**Backwards-compatibility implications.** See §8; unchanged in substance
from the first version of this document.

**Failure modes.** An author declaring two genuinely-simultaneous
transitions as two separate single-transition events (under-claiming
co-occurrence) produces a wider, more uncertain candidate set than reality
warrants — a conservative error, not a silent-wrong-answer one. The
inverse error — bundling two transitions into one event when they did not
actually happen together — is the dangerous direction, and is exactly why
§10 requires *sources* on any co-occurrence claim, not just a bare
grouping.

### Architecture 2 — First-class independent axes, cross-product states (re-evaluated under the corrected axis definition)

**Under the corrected definition, this architecture's central advantage
evaporates.** The first version of this document sold Architecture 2 on
"an axis is naturally an ordered chain, so grouping by axis gives you
chronological ordering almost for free." §1's corrected axis definition
explicitly forbids exactly that inference — axis membership and evidenced
order are now separate relations, established independently. Once that
conflation is removed, Architecture 2 has two honest options, both worse
than Architecture 1:

- **(2a) Keep axis-grouping mandatory, and *also* require every
  same-axis pair to carry an explicit chain edge** (no longer implicit).
  This is now strictly more schema than Architecture 1: it has everything
  Architecture 1 has (explicit events, explicit `ordering`), *plus* a
  mandatory, separately-maintained axis-grouping structure that duplicates
  information already recoverable from the ordering graph in the common
  case (a chain of same-labelled events) and adds no expressive power in
  the uncommon case (§1's B1-precedes-A2 example shows axis membership and
  graph edges can legitimately diverge, so the two structures cannot even
  be merged into one without losing information).
- **(2b) Let axis-grouping silently continue to imply chain order**,
  which is precisely the bug this document exists to fix, reintroduced one
  layer up (a "these are the same axis" claim instead of "this is the
  previous array entry" claim, but the same category of unevidenced
  inference).

**Conclusion: Architecture 2, correctly specified, is not a distinct
architecture any more — it is Architecture 1 plus a mandatory,
partially-redundant grouping structure.** The genuine ergonomic benefit it
offered (a reader immediately sees "this record has 2 independent
questions" from the JSON's shape) is fully recovered by Architecture 1's
existing optional `axis` label on each transition (§1), without adopting a
second computational primitive. This architecture is retained in this
document only as the worked example of *why* the corrected axis definition
matters — not carried forward as a live candidate into §3 onward, where
Architecture 1 (already covering everything 2a could offer) and
Architecture 3 are compared directly.

### Architecture 3 — Explicit historical states, transitions not stored (sum-type fix only)

Unchanged in its core mechanism from the first version of this document —
it never relied on array order (states are named, not positioned) and
never conflated axis with chain structure (it has no axis concept at all).
The one required fix is exactly what the task asked for: its
`implementation` field is now the same closed `ImplementationCoverage` sum
type defined in §4, never a bare string or an ambiguous `dict | None`.

```jsonc
{
  "id": "erratum-giant-rat",
  "states": [
    {
      "id": "goat-baseline",
      "description": "Reveal-on-whiff required; no target check at activation.",
      "plausible_when": { "on_or_before": "2011-02-02" },
      "coverage": { "kind": "reuse-upstream", "historical_passcode": 504700172 }
    },
    {
      "id": "activation-tightened-only",
      "description": "Reveal still required; activation now needs a valid target.",
      "plausible_when": { "unknown": true },
      "coverage": { "kind": "known-gap", "reason": "..." }
    },
    {
      "id": "modern",
      "description": "Neither reveal nor unconditional activation.",
      "plausible_when": { "on_or_after": "2019-04-03" },
      "coverage": { "kind": "modern" }
    }
  ]
}
```

**Co-occurrence under Architecture 3, for comparison.** This is the one
place Architecture 3 has a genuine, not merely apparent, ergonomic edge:
an author representing "A and B changed together, date unknown" simply
never writes a state where A and B differ — there is no extra machinery to
learn, because states are authored directly and a mixed state is just a
state nobody writes. The cost, as already established in the first version
of this document (§12.5) and unaffected by this revision, is that nothing
*mechanically guarantees* the author did not simply forget a state that
should exist — Architecture 3's per-case ergonomic wins are real but always
purchased with the same structural risk.

All other properties (migration complexity, ergonomics, failure modes)
are unchanged from the first version of this document and are not
repeated here; see §6 for the transition-centric-vs-state-centric
resolution, also unchanged in conclusion.

---

## 3. Proof against real records

Ten real records now, not seven: the task's own seven, plus **YZ-Tank
Dragon** (both events completely undated, and its own review notes admit
`changes[]` order was chosen "for continuity," not evidence — direct,
first-party proof this project has already made the mistake this document
exists to prevent), **Insect Imitation / Last Will** (a researcher-asserted
order claim, neither a raw date nor a disclaimed unknown), and — new in
this revision — **Sangan** (§3.J), whose corrected classification is the
concrete proof that the stricter, fully mechanical audit in §7 was
necessary, not merely thorough for its own sake.

### A. Giant Rat — the baseline stress case, and the co-occurrence non-case

Two **events**, `verification` (dated, `old_attested_through: 2011-02-02`)
and `activation-semantics` (completely undated), each with exactly one
transition, **declared as two separate events with no `ordering` entry
between them** — not because nothing links them (Giant Rat's own review
notes call them "one GOAT script encoding both ruling behaviours"), but
because *co-occurrence at a specific, even unknown, joint date* is a
stronger and different claim than *both being part of the general search-
verification question*, and nothing in the evidence asserts the former.
This is the direct proof the task asked for: **simultaneity is not
accidentally assertable** under Architecture 1 — an author would have had
to actively write both transitions inside one `events{}` entry to produce
it, and nothing about labelling them with the same `axis` (which this
document's corrected §1 definition explicitly allows without implying
order or co-occurrence) does that automatically.

At Edison (2010-04-24): `verification` is OLD (excluded from all
candidates), `activation-semantics` is AMBIGUOUS (either). Surviving
down-sets: `{}` and `{activation-semantics}` — **2 candidates**, exactly
the answer this project has already committed to (c913817), derived here
with no reliance on which of the two events happens to be written first in
the `events{}` object.

### B. A Deal with Dark Ruler — reversed declaration order relative to Giant Rat

Same two events, same axes, but written in the opposite order in the JSON
object (one of the 8 Edison cluster records where today's schema's
list-order-dependent arithmetic happens to land on the right answer by
chance). Under Architecture 1, **object key order is not read at all** —
the candidate computation depends only on event identity and the (empty)
`ordering` block, so this record and Giant Rat produce the identical
2-candidate structure regardless of which event's key is written first.
This is the point of the exercise: swapping declaration order changes
nothing, eliminating the exact defect that made 29 of the 38 Edison
records self-contradictory while the other 9 worked by accident.

### C. Paladin of White Dragon — three events, no declared order among any pair

Three single-transition events: `activation` (undated), `verification`
(bounded 2011-02-02/2019-04-03), `attack-restriction` (dated exactly
2013-09-13). **Corrected finding from §7's stricter audit:** all three
pairwise relationships are genuinely unevidenced — not just
`activation`/`verification` (the Giant-Rat-shaped bundled pair) but also
each of their relationships to `attack-restriction`, which the record's own
review notes describe only as "not reachable by either in-scope snapshot,"
never as ordered relative to the other two. `ordering: {}` — no edges
declared at all. 8 combinatorial down-sets. At Edison: `verification` OLD,
`attack-restriction` OLD (2010 < 2013), `activation` AMBIGUOUS. Surviving
down-sets: `{}` and `{activation}` — 2 candidates, matching the
already-committed, live `selection_at()` output for this record exactly.

This remains the sharpest stress case against any simpler design: a
two-valued per-transition flag cannot express "unordered relative to two
different other things for two different reasons," and neither can a
same-event grouping alone (there is no co-occurrence evidence here either —
all three stay separate events).

### D. Tyrant Dragon — mechanically-distinct, order genuinely unknown, not co-occurring

Two events, mechanically unrelated (an attack condition; a Graveyard-
revival cost timing), review notes explicit: *"cannot be sequenced against
each other because the former has no chronology at all."* No `ordering`
edge, no co-occurrence — two ordinary, separate, unordered events. At
Edison: 2 candidates (`{}`, `{extra-attack}`), matching the committed
result. At a hypothetical 2014-01-01 snapshot: 2 candidates
(`{revival-timing}`, both) — **not** self-contradictory at either
snapshot, because nothing was ever asserted about their relative order in
either direction; this is the same result the first version of this
document already established, unaffected by the event/transition
restructuring.

### E. Axe of Despair — the second order-unknown, mechanically-distinct case

Structurally identical to Tyrant Dragon; review notes silent rather than
explicit about order, which — as established in the Edison audit and
unchanged here — is not evidence of order either. Same treatment, same
result.

### F. Necrovalley — genuinely fully-dated multi-event record

Four events, every one exactly dated, in `ordering.chains: [["v1","v2",
"v3","v4"]]` — **one array, four ids, declared explicitly** (this is the
sugar §2 introduced specifically so this case does not become more
cumbersome than today's schema; it costs one field, not four annotations).
Down-set enumeration collapses to exactly 5 linear states, identical in
substance to today's `k_min..k_max` arithmetic. Re-verified under §7's
stricter test: every one of the four dates is exact (day precision), no
window overlaps any other — the chain is not merely "each event is dated,"
it is provably, mechanically ordered (§7 explains exactly how this is
checked, and why that check is not vacuous — see §3.J below for a fully-
dated-looking record that fails it).

### G. A one-change record (the common case — e.g. any of the 236 trivial records)

One event, one transition, two states (`{}` implemented per the record's
own `coverage`, `{it}` mapped to `coverage.kind: "modern"`). No `ordering`
needed at all. §13 proposes sugar so this, the overwhelming majority case,
does not pay the full event/transition nesting cost in the actual JSON on
disk.

### H. YZ-Tank Dragon — both events completely undated, and a first-party admission of the exact failure mode this document exists to prevent

Two events — a Monster-Zone contact-material restriction, a nomi-vs-semi-
nomi summoning-condition change — **neither** carrying any date or bound.
The record's own review notes: *"The relative order of the two recorded
changes is also unknown; they are chained ruling-then-functional for
continuity."* Read again in light of §2's corrected schema: this project's
own past authoring reached for a linear chain *because the old schema gave
it no other way to write the record down*, in the same breath as
disclaiming that any order was actually known. Under Architecture 1, an
author in this position writes two separate, unordered events — the
schema no longer has an implicit-chain shape to "reach for" by default,
because there is no default. `ordering: {}`. 4 down-sets, all surviving at
any snapshot before either event's (unknown) date — the widest candidate
set of any worked example in this document, correctly reflecting that this
record currently has the least evidence of any record in the corpus.

### I. Insect Imitation / Last Will — a researcher-asserted order claim

Two events each: one exactly dated, one completely undated. Review notes
assert a conclusion — *"the functional change precedes the ruling
change"* — without citing a direct source for the *order* itself (only for
each event's own date/bound). §5.6 gives this its own constraint tier
(`basis: "inferred"` or similar), distinct from both a sourced date and a
disclaimed unknown, so a future author can record *why* the order is
believed without silently promoting it to the same weight as a citation.
Whether that inferred order, once tagged, should license an `ordering`
edge is a per-record judgement call this document still leaves to a human
reviewer (§7) — not resolved here, and not force-classified either way.

### J. Sangan — fully dated, still not fully ordered (the finding that forced the stricter audit)

**New in this revision.** Two events: `verification` (bounded
2011-02-02/2019-04-03, the classic search-verification-package interval —
mechanically unrelated to Giant Rat's activation axis for this card, since
Sangan's own review notes establish "there is no relaxed-activation
component to leave undated" for this card specifically), `name-lock`
(dated exactly 2016-09-15, a once-per-turn/name-lock functional erratum,
mechanically unrelated to `verification`). At first glance this looks like
§3.F (Necrovalley) — "every event has some dating information" — and the
first version of this document classified it exactly that way,
`fully-ordered-multi-transition`, on that test alone.

**It is not.** `name-lock`'s exact date, 2016-09-15, falls *inside*
`verification`'s bounded interval (2011-02-02 .. 2019-04-03). At a
snapshot of 2016-09-15 or later (but before 2019-04-03), live
`selection_at()` returns `candidates=(1, 2)` — and candidate 1, under
today's schema's positional semantics, formally means "the first-listed
transition (`verification`) has occurred, the second (`name-lock`) has
not" — which **directly contradicts `name-lock`'s own confirmed NEW status
at that exact snapshot.** The *real* two candidate states at such a
snapshot are `{verification=OLD, name-lock=NEW}` and
`{verification=NEW, name-lock=NEW}` (modern); today's schema has no valid
index for the first of these and mislabels its second candidate's slot
with an entry (`historical_passcode: 511002631`) that is not empty — so,
unlike Giant Rat, this does not currently surface as a validator-visible
gap. It would surface as a **silently wrong historical substitution** if
any future format's `unresolved_policy` or explicit include ever pinned
"version 1" for a snapshot inside this window. Verified directly against
live code (not merely reasoned about): see §7 for the exact mechanical
check, run against the full 296-record corpus, that found this.

Under Architecture 1: two separate events, `ordering: {}` (their relative
order is exactly as unevidenced as Tyrant Dragon's — nothing in Sangan's
own review notes claims otherwise). Down-set enumeration produces the
*correct* 2-candidate set at every snapshot, including 2016-09-15 onward,
with no positional mislabeling possible, because there is no position to
mislabel — states are keyed by which events occurred, not by how many.
`Witch of the Black Forest` has the identical shape and is treated
identically in §7.

**Why this record matters more than another Edison-shaped example.** It
is proof that "does every event have some dating information" is *not* a
sufficient test for "is this record safe under today's schema" — the
correct test is whether the dated intervals are mutually
non-overlapping (§7), and Sangan shows a record that looks, and was
initially classified as, completely unremarkable can still carry the
identical defect this whole document exists to fix.

---

## 4. Implementation coverage is an explicit sum type

**Corrected.** The first version of this document's `HistoricalState.
implementation: dict | None` was exactly the ambiguity the task flagged:
some examples used `None` to mean "unreachable," others left it implicit
that a live example used `"modern"` as a bare string. Replaced with one
closed representation, used identically by every architecture in §2 and by
the API in §9:

```python
class Coverage(Enum):
    MODERN = "modern"                 # the terminal state; cards.cdb IS the implementation
    REUSE_UPSTREAM = "reuse-upstream"
    CUSTOM_SCRIPT = "custom-script"
    NONE_NEEDED = "none-needed"
    KNOWN_GAP = "known-gap"           # confirmed missing; reason + sources required
    UNRESOLVED = "unresolved"         # not yet investigated

@dataclass(frozen=True)
class ImplementationCoverage:
    kind: Coverage
    historical_passcode: int | None = None   # REUSE_UPSTREAM / CUSTOM_SCRIPT only
    upstream: str | None = None
    script: str | None = None
    gap_reason: str | None = None            # KNOWN_GAP only
    gap_sources: tuple[str, ...] = ()        # KNOWN_GAP only

@dataclass(frozen=True)
class HistoricalState:
    events: frozenset[str]
    label: str
    coverage: ImplementationCoverage   # NEVER None, NEVER a bare string, for a real candidate
```

**The completeness rule (also closing §5 of the task, "recheck state-map
completeness"), stated once, unambiguously, and used everywhere in this
document — corrected in this pass to name an exception that was previously
implied inconsistently rather than stated (adversarial review caught this:
§2's example, §3.G, §10 invariant 5, and §13's flattening sugar all
*already* treated the terminal state as automatically `MODERN`, while this
rule's first drafting said absence *always* means `UNRESOLVED` with no
exception — the two cannot both be true, and the fix is to name the
exception explicitly rather than leave it an unstated, if consistently
applied, special case):**

> A `HistoricalState` only exists (is only ever constructed and offered as
> a candidate) for a down-set the ordering/co-occurrence graph can actually
> produce. **Exactly one down-set — the one containing every event — is
> exempt from everything below: it is structurally, unconditionally
> `ImplementationCoverage(kind=MODERN)`, never authored and never
> defaulted, because "every known transition has occurred" is definitionally
> what the shipped `cards.cdb` entry already represents — there is nothing
> to research or resolve about it, so `UNRESOLVED` could never correctly
> describe it. An author who writes a `states[]` entry for this down-set
> anyway must write `coverage.kind: "modern"` (the validator rejects any
> other value there, per §10 invariant 5) — writing one at all is
> permitted documentation, never required.** For every *other* down-set:
> if the record's authored `states[]` contains a matching entry, its
> `coverage` is used verbatim. **If it does not, the down-set's coverage is
> `ImplementationCoverage(kind=UNRESOLVED)` — mechanically, always, with no
> other meaning attachable to an absent entry.** A structurally-impossible
> down-set (one the ordering/co-occurrence graph forbids) is never
> constructed as a `HistoricalState` at all, and therefore never needs a
> `coverage` of any kind, explicit or defaulted.

This directly satisfies the task's requirement: "there must be no semantic
distinction encoded merely as entry absent unless the absence has exactly
one formally-defined meaning" — here, absence has exactly one meaning for
every down-set except the single, structurally-identifiable terminal one,
which is called out by name rather than left as a silent special case.
§13's flattening sugar (a record with one `coverage` field and no
`states[]` at all) is consistent with this: the sugared record's single
authored `coverage` describes the *baseline* (`{}`) down-set, and the
terminal down-set's `MODERN` coverage is synthesised by the exception
above, not read from anywhere in the sugared JSON — exactly as the
exception says it should be.

**Giant Rat's full 2×2, worked through completely under this rule** —
requested explicitly by the task:

```
                    activation-semantics
                    OLD                       NEW
verification  OLD   {} -> REUSE_UPSTREAM       {activation} -> KNOWN_GAP
                    (authored, 504700172)      (authored, "no upstream
                                                 implementation exists for
                                                 a state where only one
                                                 had changed")

              NEW   {verification} -> ???      {verification,activation}
                    NOT authored in the         -> MODERN
                    real record. Mechanical      (structurally required)
                    default: UNRESOLVED.
                    Structurally reachable
                    (no ordering edge forbids
                    it) but never a candidate
                    at the Edison snapshot
                    specifically, because
                    `verification` is
                    confirmed OLD there.
```

The bottom-left cell is the one worth dwelling on, because it is exactly
the cell the first version of this document's "coincidence" language
danced around: it is a real, structurally-valid `HistoricalState`
(nothing forbids `verification` from having occurred while
`activation-semantics` has not), it simply has never been a *candidate* at
any snapshot this project has queried, and it has never been *authored*
either — so under this document's rule it is `UNRESOLVED`, not silently
absent from the model and not silently equal to any other cell. A future
snapshot where `verification` is confirmed NEW while `activation-
semantics` remains genuinely ambiguous (not the shape Edison happens to
be) would surface it as a real, correctly-labelled `UNRESOLVED` candidate
— never as a mislabelled substitute for a different cell, which is exactly
the failure §3.J found in Sangan's real data.

**Scaling beyond 2×2.** Unchanged in kind from the first version of this
document — the down-set/event-set space grows combinatorially with events
actually present (§7's corpus scan: never more than 4), and every cell,
authored or defaulted, is unambiguous under the rule above regardless of
how large the space gets.

---

## 5. Historical constraints — expanded to seven kinds

1. **Exact event date** (`effective.date` + `precision`) — unchanged.
2. **Bounded attestation** (`old_attested_through` / `new_attested_from`)
   — unchanged; this is what makes Giant Rat's `verification` event
   determinate at Edison without an exact date, and — per §3.J — what
   makes Sangan's `verification` event dangerous once a snapshot lands
   inside its window while another event has already resolved inside that
   same window.
3. **Explicit known-before/known-after between two named events** — the
   `ordering.edges`/`chains` mechanism (§2). The *only* source of order in
   the corrected model; never inferred from declaration position.
4. **Explicit "relative order is unknown"** — the default (§1), now
   positively true of every event pair unless (3) is declared, not merely
   true of pairs an author forgot to think about. Corpus evidence for this
   tier: the "cannot be sequenced" language already present, independently
   worded, in the review notes of the vast majority of the 48 records
   found in §7.
5. **Co-occurrence: two or more transitions belonging to one event** —
   corrected from the first version of this document's "labelling fact
   more than a constraint fact" framing. It is a **first-class chronology
   fact now**, not merely documentation — it removes real candidate states
   from the down-set space (§2's `policy-revision` worked example: 2
   states instead of 4), which the first version of this document's
   `bundled-independent-axis` label never actually did (it computed
   identically to plain "order unknown," §3.A/§3.D of the prior revision
   showed this explicitly). This is the corrected understanding: what
   looked like a labelling-only distinction in the prior revision was
   actually a symptom of not yet having co-occurrence as a real mechanism
   at all — with one now available, some records currently read as
   "bundled, order-unknown, 4 theoretical states" may, on a case-by-case
   research basis, actually turn out to be genuine co-occurrence (2
   states) once a reviewer asks the question directly. This document does
   not reclassify any specific record on this basis (that is exactly the
   "do not choose the schema/reclassify data in this documentation task"
   line the earlier task explicitly drew) — it flags the question as a
   new, real research avenue §7's migration work should ask per bundled
   record, not resolve it here.
6. **Order asserted by researcher inference, not by a direct source** —
   unchanged from the first revision, surfaced by Insect Imitation/Last
   Will (§3.I). Recommendation unchanged: a `basis` field distinguishing
   it from both a cited date and a disclaimed unknown.
7. **Exact-date simultaneity** — two events (or, more precisely, since
   simultaneity is now representable directly via co-occurrence, two
   transitions an author has *not* chosen to merge into one event, but
   which happen to carry the identical exact date) — handled by the
   ordinary event-dating machinery with no special case needed: if two
   separate events both have `effective.date` equal, their OLD/NEW status
   is always identical at every snapshot regardless of any declared
   `ordering` edge between them, and declaring one is optional
   documentation, not a correctness requirement (§12.6 stress-tests this
   directly). The distinction from (5) is deliberate: two events with the
   same exact date are still *two* events (each could, in principle, be
   later found to have actually differed by a day once more research is
   done) — true co-occurrence (5) is a stronger claim, that they are not
   merely dated identically but are genuinely one occurrence.

**The non-negotiable principle, restated and now enforced by construction
rather than by convention:** UNKNOWN must remain UNKNOWN. §4's coverage
rule and this section's ordering rule work together to guarantee it — a
down-set is never excluded from the candidate space without either a
declared `ordering` edge or a co-occurrence grouping backing the
exclusion, and a candidate's coverage is never silently anything other
than `UNRESOLVED` without an authored entry.

---

## 6. Transition-centric vs. state-centric: is either primary?

Unchanged in conclusion from the first version of this document, restated
precisely for the corrected model: **event-and-transition-centric for
chronology, state-centric for implementation coverage — a hybrid, not a
compromise, and not a fourth architecture.** The one refinement this
revision adds: it is specifically *events*, not bare transitions, that are
the right chronology-centric primitive, because the evidence this project
actually has is evidence about occurrences (when did something happen,
did two things happen together), and a bare transition — a "what changed"
fact with no independent "when" of its own — was never the right unit to
attach chronology evidence to in the first place. This is why Architecture
1's revision in §2 is not merely "the same design with array-order
removed" but a genuine restructuring: separating "what changed" (a
transition, nested, chronology-free) from "when it happened" (an event,
the DAG node) turned out to be necessary to fix all four of the problems
this revision addresses, not just the array-order one.

---

## 7. Migration analysis — corrected with a fully mechanical test

**The first version of this document's test was too weak, and this
section exists specifically to correct it.** It classified a
multi-transition record as `fully-ordered-multi-transition` whenever
"every relevant change has some dating information" — sufficient to notice
Giant Rat's shape (one event totally undated) but *not* sufficient to
notice Sangan's (every event dated, but two dated windows overlapping),
because it never checked whether the dated intervals were actually
mutually exclusive.

**The corrected, fully mechanical test**, run against every one of the 296
records, not sampled: for every record with 2+ implementation-relevant
transitions, sweep a wide range of candidate snapshots (each transition's
own date/bounds ± a buffer, plus a yearly sweep from 2000 to 2030 to catch
anything the transitions' own dates don't suggest); at every snapshot
where `selection_at()` reports `state="ambiguous"`, check every candidate
index `k` against every relevant change's own, independently-computed
OLD/AMBIGUOUS/NEW status: candidate `k` claims relevant changes `0..k-1`
have occurred and `k..end` have not; if any change in the "has occurred"
set is independently confirmed OLD, or any change in the "has not"
set is independently confirmed NEW, that candidate is self-contradictory.
This is precisely the mechanical form of "does chronology actually prove
every edge" the task asked for, and it requires no judgement calls — it is
a pure consistency check between what the candidate label formally asserts
and what each transition's own dating evidence says.

**Result: 48 of 296 records fail this check, not 44.** The 44 already
established by the Edison audit, plus four more found only by running this
check corpus-wide rather than relying on "does every transition have some
date": **Sangan, Witch of the Black Forest** (§3.J — both events dated,
windows overlap), and **Insect Imitation, Last Will** (§3.I — already
flagged as borderline in the prior revision; this mechanical check
confirms they belong in the affected population, not merely near it).

| Category | Records | Change from prior revision |
|---|---|---|
| Trivial (0-1 relevant changes) | **236** | unchanged |
| Genuinely, mechanically fully-ordered | **11** | down from 13 — Sangan and Witch of the Black Forest removed, reclassified below |
| Bundled/independent-axis (Edison cluster-1: 38; YZ-Tank Dragon: 1) | **39** | unchanged |
| Mechanically-distinct, order-unknown (Edison non-cluster: 6; Sangan, Witch of the Black Forest: 2) | **8** | up from 6 |
| Needs manual review (researcher-inferred order: Insect Imitation, Last Will) | **2** | unchanged in count, now backed by the mechanical check rather than informal reading alone |
| **Total** | **296** | 236 + 11 + 39 + 8 + 2 = 296 |

**The 11 genuinely fully-ordered records**, re-verified individually
against the mechanical check (zero self-contradictory candidates at any
swept snapshot): Blackwing - Sirocco the Dawn, Blue-Eyes Toon Dragon,
Blue-Eyes Ultimate Dragon, Dark Necrofear, Necrovalley, Night Assailant,
Rescue Cat, Soul Rope, Swords of Concealing Light, Toon Mermaid, Toon
Summoned Skull. Ten of these eleven carry only exact, day-precision dates
throughout (order is then a direct, trivial comparison of the dates
themselves, not an inference — §12.6 explains why this case can never fail
the check by construction); the eleventh, Rescue Cat, has one bounded
event whose window closes entirely before its dated sibling begins
(2008-12-15 < 2017-03-30, no overlap, order genuinely proven despite the
imprecision).

**Why 48, not just "44 plus 4 more,"** matters for the migration plan: it
confirms the task's own instruction — do not trust the Edison-scoped 44/85
as the entire affected population — was correct, and shows *why* a
scoped, format-specific audit (Edison's) cannot be trusted to find every
instance of a corpus-wide representational defect, even when it is
unusually thorough within its own scope. The mechanical check in this
section is format-independent; it does not care whether any
currently-defined format's snapshot happens to expose a given record's
defect, which is exactly why it found Sangan (whose defect is invisible at
GOAT and Edison, both of which precede the overlap window) and would find
the next one too, whenever this project adds a format whose snapshot lands
somewhere the four already-known-safe-looking records above have never
been queried.

**Migration proof burden, revised under the no-implicit-order rule (§2).**
Because omitted ordering means no edge, a migration script cannot simply
copy `changes[]` order into `ordering.chains` for every record — doing so
would silently reintroduce exactly the array-order-as-evidence bug this
document exists to remove, for any of the (currently unknown, and
unknowable without per-record research) records whose list order does
*not* reflect a real evidenced sequence. The correct mechanical migration
procedure, by category:

- **236 trivial**: no `ordering` possible or needed (single event) — pure,
  safe rename.
- **11 fully-ordered**: the migration script **emits `ordering.chains`
  only where it can independently re-derive the order from the dates
  themselves** — i.e. it re-runs the same non-overlap check used to find
  this category, and only writes an edge where that check *passes*, never
  by copying `changes[]` position. For all 11, this reduces to "sort by
  date, chain the sorted order" — safe, because the sort order and the
  proof are the same computation.
- **39 bundled/independent-axis + 8 mechanically-distinct order-unknown**:
  the migration script emits **no `ordering` edges at all** and, for the
  39, emits explicit event-grouping per the already-published Edison
  classification (no new research needed — already done and committed);
  the `chains`-from-`changes[]` array-copy the naive approach would
  produce is exactly what must *not* happen for these 47 records.
- **2 needs-manual-review**: blocked on a human decision (§5.6) before any
  mechanical emission — the script must not guess.

**Do not trust the Edison 44/85 as the entire affected population** — now
proven, not merely asserted: the mechanical check found 4 records entirely
outside Edison's known-wrong/divergence set with the identical defect,
none of which currently produce a *visible* symptom for any
currently-defined format, exactly the risk this document's introduction
describes.

---

## 8. Backwards compatibility

Unchanged in conclusion from the first version of this document — option
(D), normalise both schema shapes into one internal representation during
migration, converging to (B), schema-v2-only, once every record has been
touched; not (C), a permanent dual-schema state. The one addition this
revision makes: §7's migration-proof burden means the "normalise" step in
(D) is not a passive re-shaping of v1 data into v2 structures. **49
records, not 247, need an active research step before they can be
migrated at all**, split into two disjoint groups (§7): 47 (39 bundled +
8 mechanically-distinct order-unknown) whose research is *already done* —
the Edison audit's and this document's own corpus re-audit's
classifications are the research, migration only needs to transcribe
them — and a separate 2 (Insect Imitation, Last Will) whose research is
*not yet done at all*, blocked on a human choosing which §5 constraint
tier their researcher-inferred order claim belongs to before any
annotation, mechanical or otherwise, can be written. This does not change
the recommended option, only
sharpens what "migrate" means for those specific 47 records versus the 247
that really are a mechanical rename.

---

## 9. Selection API design — chronology and implementation coverage as separate dimensions

**Corrected.** The first version of this document's `ErratumSelection.
outcome: "determinate" | "ambiguous" | "gap" | "modern"` mixed two
independent questions — is the *chronology* determinate, and what
*coverage* does each candidate have — into one enum, which cannot cleanly
represent the task's own posed mixed case (ambiguous chronology, one
candidate implemented, one a known gap). Split into two dimensions:

```python
@dataclass(frozen=True)
class HistoricalState:
    events: frozenset[str]           # event ids applied in this state
    label: str                       # human-readable, generated
    coverage: ImplementationCoverage # §4 — never absent for a real candidate

@dataclass(frozen=True)
class ErratumSelection:
    chronology: str                          # "determinate" | "ambiguous" -- ONLY this dimension
    candidates: tuple[HistoricalState, ...]   # always the full plausible set; len == 1 iff determinate
    modern_state: HistoricalState             # the terminal state, for "is modern among candidates"

    @property
    def is_modern(self) -> bool:
        return self.chronology == "determinate" and self.candidates[0] is self.modern_state

    @property
    def modern_is_possible(self) -> bool:
        return self.modern_state in self.candidates

    @property
    def has_known_gap(self) -> bool:
        return any(c.coverage.kind is Coverage.KNOWN_GAP for c in self.candidates)

    @property
    def needs_implementation_research(self) -> bool:
        return any(c.coverage.kind is Coverage.UNRESOLVED for c in self.candidates)
```

No third or fourth top-level enum value is needed — `"gap"` and
`"modern"` are no longer chronology states at all, they are properties of
individual candidates' `coverage`, queried via the helpers above. This is
deliberately *not* a single combined enum, per the task's own challenge:
a single enum cannot represent "ambiguous chronology, candidate A
implemented, candidate B a known gap" without either inventing a fifth
value for every new combination of {chronology status} × {coverage kind
present among candidates}, or silently picking one candidate's coverage to
report and discarding the other's — both worse than two small, orthogonal
fields plus derived booleans.

Five example returned structures, one per case the task names:

```python
# Determinate modern
ErratumSelection(
    chronology="determinate",
    candidates=(HistoricalState(events=frozenset({"e1", "e2"}), label="modern",
                                 coverage=ImplementationCoverage(kind=Coverage.MODERN)),),
    modern_state=HistoricalState(events=frozenset({"e1", "e2"}), label="modern",
                                  coverage=ImplementationCoverage(kind=Coverage.MODERN)),
)

# Determinate historical (Necrovalley between two of its four dated events)
ErratumSelection(
    chronology="determinate",
    candidates=(HistoricalState(events=frozenset({"v1"}), label="v1 negation scope",
                                 coverage=ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=...)),),
    modern_state=HistoricalState(events=frozenset({"v1", "v2", "v3", "v4"}), label="modern",
                                  coverage=ImplementationCoverage(kind=Coverage.MODERN)),
)

# Ambiguous two-state (Giant Rat at Edison)
ErratumSelection(
    chronology="ambiguous",
    candidates=(
        HistoricalState(events=frozenset(), label="both old (baseline)",
                         coverage=ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=504700172)),
        HistoricalState(events=frozenset({"activation-semantics"}), label="verification=old, activation=new",
                         coverage=ImplementationCoverage(kind=Coverage.KNOWN_GAP, gap_reason="...")),
    ),
    modern_state=HistoricalState(events=frozenset({"verification", "activation-semantics"}), label="modern",
                                  coverage=ImplementationCoverage(kind=Coverage.MODERN)),
)
# .has_known_gap -> True; .modern_is_possible -> False

# Known implementation gap alone (determinate chronology, missing implementation)
ErratumSelection(
    chronology="determinate",
    candidates=(HistoricalState(events=frozenset({"activation-semantics"}), label="verification=old, activation=new",
                                 coverage=ImplementationCoverage(kind=Coverage.KNOWN_GAP, gap_reason="...")),),
    modern_state=HistoricalState(events=frozenset({"verification", "activation-semantics"}), label="modern",
                                  coverage=ImplementationCoverage(kind=Coverage.MODERN)),
)

# Multi-axis ambiguity (Paladin at a hypothetical fully-ambiguous snapshot)
ErratumSelection(
    chronology="ambiguous",
    candidates=(  # up to 8 HistoricalState entries, one per surviving down-set
        HistoricalState(events=frozenset(), label="all old",
                         coverage=ImplementationCoverage(kind=Coverage.REUSE_UPSTREAM, historical_passcode=...)),
        HistoricalState(events=frozenset({"activation"}), label="activation=new only",
                         coverage=ImplementationCoverage(kind=Coverage.UNRESOLVED)),
        HistoricalState(events=frozenset({"attack-restriction"}), label="attack-restriction=new only",
                         coverage=ImplementationCoverage(kind=Coverage.UNRESOLVED)),
        # ... up to 5 more, filtered by whichever events are actually AMBIGUOUS at this snapshot
    ),
    modern_state=HistoricalState(events=frozenset({"activation", "verification", "attack-restriction"}), label="modern",
                                  coverage=ImplementationCoverage(kind=Coverage.MODERN)),
)
```

**The mixed case the task explicitly poses** — "ambiguous chronology with
candidate A implemented and candidate B a known implementation gap" — is
exactly Giant Rat's own example above: `chronology="ambiguous"`, two
candidates, `candidates[0].coverage.kind is Coverage.REUSE_UPSTREAM`,
`candidates[1].coverage.kind is Coverage.KNOWN_GAP`,
`selection.has_known_gap` is `True`, `selection.modern_is_possible` is
`False`. Nothing about this required a combined enum value; every fact is
independently and unambiguously readable.

---

## 10. Validation design

Ten invariants, three of them substantively changed from the first version
of this document:

1. **Every `ordering` reference names a real event id** — unchanged, still
   new relative to today's schema.
2. **No cycles in `chains`/`edges`** — unchanged; standard topological
   sort, and, per the task's explicit instruction, **declaration order of
   events plays no role in validity** — an `ordering` entry may reference
   an event declared anywhere in `events{}`, forward or backward, and
   cycle detection is the only thing that can reject a set of edges, not
   the order they or the events they reference happen to be written in.
3. **Every `states[]` entry is a down-set the ordering/co-occurrence graph
   can actually produce** — unchanged in spirit, re-scoped to events.
4. **No duplicate state keys** — unchanged.
5. **The all-events state is unambiguously `coverage.kind == MODERN`, and
   no other state may be** — unchanged in spirit, now phrased against the
   sum type (§4) rather than an informal `"modern"` string.
6. **CORRECTED, now the primary check, not a lint: the exact mechanical
   overlap test from §7**, run at validation time, not just during a
   one-off corpus audit. For every pair of events with no declared
   `ordering` edge between them, the validator computes both events'
   OLD/AMBIGUOUS/NEW status across a snapshot sweep (mirroring §7's
   method) and asserts that no `states[]`-authored candidate — nor any
   *mechanically defaulted* `UNRESOLVED` candidate — is ever
   self-contradictory relative to either event's own independently-computed
   status. This is what §7 ran as a one-time corpus audit; **as a
   validator invariant it runs on every future `validate` invocation**,
   which is what actually prevents the next Sangan from being merged
   silently — a text-matching lint (this revision's predecessor's
   proposal) would not have caught Sangan at all, since Sangan's review
   notes never used "cannot be sequenced" language; only the mechanical
   check does.
7. **Every declared `ordering` edge that contradicts dated evidence is
   rejected** — generalises today's `erratum.changes-out-of-order` check:
   if event B declares `after: [A]` but B's earliest possible date
   precedes A's latest possible date, that is a direct, structural
   contradiction between the declared edge and the dated evidence, hard
   error.
8. **Unreachable state mappings are detected** — unchanged.
9. **Ambiguity cannot silently fall back unless policy explicitly allows
   it** — unchanged in principle from today's `format.erratum-ambiguous`/
   `unresolved_policy` handling, operating over `ErratumSelection.
   candidates` (§9) instead of integers.
10. **Co-occurrence claims require sources**, per §2's failure-mode note —
    an `events{}` entry with 2+ transitions must cite `sources` supporting
    the co-occurrence claim specifically, not merely sources for each
    transition's own content, since asserting two things happened together
    is evidentially a stronger claim than asserting each happened.

Invariant 6 is the one this revision adds real teeth to. It is not a
heuristic tuned to Edison's specific review-note phrasing; it is the same
mechanical procedure §7 used to find Sangan and Witch of the Black Forest,
generalised to run continuously rather than as a one-time audit.

---

## 11. Build impact (traced, not modified)

Unchanged in file list from the first version of this document, updated
in *what changes per file* to reflect the event/transition split and the
sum-type coverage:

| File | What would change |
|---|---|
| `schemas/erratum.schema.json` | New `events{}` (keyed dict, not array — replaces `changes[]`), each with `effective` + `transitions[]` (no per-transition chronology); new `ordering.chains`/`ordering.edges`; new `states[]` keyed by event-id-sets with the `Coverage` sum type (§4) replacing today's `implementation.strategy` informally-typed shape; `changes[]` retained during the (D) transition period (§8). |
| `retroformats/model.py` | `Erratum.relevant_changes()`/`implementation_for_version()`/`selection_at()` replaced by event-down-set enumeration + state lookup (§2, §9); `change_state_at()` reused, now applied to an event's `effective` block instead of a bare change's. |
| `retroformats/validate.py` | `_validate_errata`'s ordering check generalised per §10.7; §10.6's mechanical overlap check is new; every integer-based `selection.version_index`/`.candidates` consumer becomes a `HistoricalState`/`Coverage` consumer; `format.erratum-include-wrong-version`/`-redundant` become event-set-equality checks instead of `== 0`. |
| `retroformats/lflist.py` | Smallest-touched of the three code files, as in the first version of this document — `select_applicable_errata()` and `baseline_override()`/`parity_override()` operate on `.chronology`/`.candidates[0].coverage` directly; `parity_override()`'s "walk in order, take first usable" logic needs a defined canonical walk order over states for a non-chain record (recommendation unchanged: fewest events applied first, ties broken by event id — degenerates to today's behaviour for every genuine chain). |
| Importers | Unaffected — no importer currently generates multi-event records. |
| Report output (`cli.py` `report -v`) | Cosmetic — prints state labels instead of version integers. |
| Tests | `OrderingConstraintTest` and `test_giant_rat_selection_shape` rewritten against corrected semantics (unchanged conclusion from the first revision) — plus **new** regression tests for Sangan and Witch of the Black Forest specifically, since those two were not previously known to need one. |
| Existing JSON records | Per §7 (corrected): 247 records (236 trivial + 11 genuinely fully-ordered) migrate via a script that **proves** each `ordering.chains` edge it emits rather than copying `changes[]` position; a separate 47 records (39 bundled + 8 mechanically-distinct order-unknown) need explicit event-grouping/no-ordering annotation, all already researched (Edison audit + this document's own corpus re-audit — no new research needed for these 47); a further, disjoint 2 records (Insect Imitation, Last Will) are not yet researched at all and are blocked on a human §5.6 decision before any annotation can be written. |
| Generated `dist/` output | Must not change for any currently-defined format — the same regression gate as the first version of this document, unaffected by this revision's corrections. |

---

## 12. Adversarial review

Re-run against the corrected (event-DAG) Architecture 1, with the two new
required stress cases (co-occurrence, and deliberately wrong co-occurrence)
added.

**1. Three independent binary axes.** Three single-transition events, no
`ordering`, no co-occurrence — 2³ = 8 down-sets, mechanically generated,
unchanged from the first revision's analysis.

**2. Partial ordering: A < C, B unordered relative to both.** Native:
`ordering.edges: [{"before": "A", "after": "C"}]`, nothing declared for
B. Unchanged conclusion from the first revision — still the sharpest test
against a two-valued flag, which still cannot express it (see the
retraction below).

**3. Two transitions whose order becomes known later.** An edit adding an
`ordering.edges` entry; unchanged.

**4. Multiple transitions on the same behavioural axis.** **Materially
different under the corrected model, and worth stress-testing explicitly
this time.** Because axis membership no longer implies order (§1), two
events sharing an `axis` label (e.g. two successive revisions of
Necrovalley's negation scope) require an *explicit* `ordering.chains`
entry to be treated as sequential — sharing a label alone produces two
unordered events, which is *correct* behaviour (the corrected model
refuses to guess an order from a label the way the first revision's
Architecture 2 would have), but it means an author who mislabels two
same-axis events without also chaining them gets a *wider*, more
conservative candidate set than intended, not a wrong one. This is the
direct trade-off §2 already flagged: safety over silent convenience.

**5. State implementations missing for only some, non-contiguous
combinations.** §4's Giant Rat 2×2 already exercises this fully under the
corrected sum type; unchanged conclusion (Architecture 3's completeness
weakness here is real and unaffected by this revision).

**6. Two transitions on the same exact date — the "same date" vs.
"same event" distinction, stress-tested directly.** Two events, `A` and
`B`, each with `effective.date: "2015-06-01"`, no co-occurrence declared.
At every snapshot, `change_state_at()` gives both events identical
OLD/NEW status (day-precision boundaries are deterministic and identical
for identical dates), so no `ordering` edge is *required* for correctness
— §10.6's mechanical check never fires a contradiction for this pair,
because their independently-computed statuses can never disagree. This is
different from declaring them one *event*: two same-dated-but-separate
events still, in principle, permit a future finding that they were not
actually simultaneous (a day-precision date is not a certificate of
atomicity) — merging them into one event is a stronger, evidentially
distinct claim (§5.7), and this stress case confirms the model does not
force that stronger claim just because the dates happen to match.

**7. Cosmetic changes interspersed with behavioural ones.** Unaffected —
`kind in {functional, ruling}` filtering happens per-transition, before
any transition's parent event enters the down-set machinery; an event
containing only cosmetic/engine transitions never creates a distinguishable
state, identical in effect to today's filtering.

**8. An engine-level behaviour rather than a card-script behaviour.**
Unchanged — explicitly out of scope, not unified with rule-profile
modelling in this document.

**9. Future chronological formats querying dates far outside GOAT/
Edison.** Strengthened, not just repeated: §3.J's Sangan finding is a
*real* instance of this exact risk materialising in already-shipped data,
not a hypothetical — proof that the risk this stress case describes is not
theoretical.

**10. NEW — deliberate/mistaken co-occurrence.** What stops an author from
wrongly merging two unrelated transitions into one event, asserting a
false simultaneity? Nothing purely structural — this is a genuine, open
failure mode, honestly assessed rather than papered over: §10's invariant
10 (co-occurrence requires its own sources, not just per-transition
sources) raises the evidentiary bar but cannot mechanically verify the
claim is *true*, only that it was *asserted with support*. This is
symmetric with Architecture 2's now-retired "mis-drawn axis boundary"
failure mode (§2) — human judgement is still required somewhere in this
model, and this document does not claim otherwise; it only claims the
model no longer produces *false* co-occurrence *by default*, which is the
property that actually matters (§3.A's Giant Rat non-case).

**11. NEW — a genuine co-occurrence case, mechanically confirmed correct.**
Re-verified computationally (not merely reasoned about) for §2's
`policy-revision` worked example: with one event and two transitions,
`selection_at()`-equivalent down-set enumeration produces exactly 2 states
(`{}`, `{policy-revision}`) at every snapshot, never 4 — confirmed by
direct construction of the down-set algorithm against this shape, since no
real corpus record currently has this exact structure to test against
live code (a gap noted honestly: this is the one case in this document's
proof set that could not be cross-checked against `retroformats/model.py`
directly, because no such record exists yet to load).

**The two-valued `order: "chained" | "independent"` marker, re-examined
under the corrected model, fails on two independent grounds now, not
one.** It could not express case 2 (partial order) in the first revision;
under this revision it *also* cannot express co-occurrence (case 11) at
all — a boolean per-transition flag has no third state for "this
transition's timing is not merely unordered relative to its neighbour, it
is identical to it, by the same historical act." Retracted on both
grounds, not just the one the first revision identified.

**State-space explosion.** Unchanged conclusion — §7's corpus-wide,
mechanical (not sampled) scan found the same maximum of 4
implementation-relevant transitions on any real record; the realistic
worst case remains 2⁴ = 16 states, and a generously tripled hypothetical
ceiling (10 transitions) remains 2¹⁰ = 1024, still negligible. Not a design
constraint worth optimising against.

---

## 13. Recommendation

**The historical-event DAG (§2's revised Architecture 1) — events as
explicitly, evidence-only ordered nodes, each carrying one or more
behavioural transitions, plus implementation coverage as an explicit sum
type keyed by event-set — is the recommended design.** The core shape
(transition/event-centric chronology + state-centric implementation
coverage) is unchanged from the first version of this document; what
changed is fixing four real defects in how that shape was specified: no
implicit ordering, explicit co-occurrence, a corrected axis definition,
and a closed coverage type.

**Original vs. refined, compared directly, per the task's explicit
request:**

| | Original (bb2c6a7): flat transition DAG | Refined (this revision): historical-event DAG |
|---|---|---|
| Chronology carrier | each transition has its own `effective` | each **event** has one `effective`; transitions are chronology-free |
| Default when order omitted | chains to previous array entry (the bug) | no edge at all (corrected) |
| Co-occurrence | not representable (only same-exact-date coincidence) | first-class: 2+ transitions in one event |
| Axis | conflated with "maximal chain" | pure semantic label, decoupled |
| Giant Rat, Paladin, Tyrant Dragon | correctly modelled | correctly modelled, unchanged |
| Sangan-shaped records | not specifically tested; would have been mis-migrated by array-copy | caught by §7's mechanical audit; correctly modelled |
| Extra authoring cost | none beyond `after: []` on exceptions | one nesting level (`events{}` → `transitions[]`) on every record, mitigated by sugar (below) |

The refined version costs a small, constant amount of extra nesting on
every record (even the simple ones) relative to the original proposal, in
exchange for removing an entire class of defect the original proposal's
array-order default would have reintroduced at the schema level. **This is
judged worth it**: the whole point of this milestone is to stop trusting
implicit structure to carry evidentiary weight, and a design that asks an
author to type one extra nesting level is a small price for a design that
cannot silently regress into the bug it exists to fix.

**Mitigating the extra nesting for the common case (247 of 296 records):**
a single-event, single-transition record may use flattened sugar —

```jsonc
{
  "id": "erratum-simple-card",
  "event": { "effective": {...}, "kind": "functional", "summary": "..." },
  "coverage": {...}
}
```

— which desugars to exactly the one-event, one-transition, two-state shape
of §3.G, with no `events{}`/`ordering`/`states[]` nesting visible in the
common-case JSON at all. This recovers, for 83% of the corpus, authoring
ergonomics at least as simple as today's schema, while the full
`events{}`/`ordering`/`states[]` shape is only ever necessary for the 49
records (§7: 47 needing explicit annotation + 2 needs-manual-review) that
already require a human to think carefully about ordering.

**Why more correct than the alternatives.** Architecture 3 cannot
guarantee state-space completeness (§4, §12.5) and has no representation
for co-occurrence beyond "the author happened to write the right two
states" (§2's Architecture 3 section). Architecture 2, correctly specified
under §1's corrected axis definition, collapses into "Architecture 1 plus
a redundant grouping layer" (§2) — not a distinct, competitive design once
the conflation that made it attractive is removed.

**Migration strategy.** §8's (D)→(B) plan, unchanged in shape; §7's
corrected, per-category proof burden governs what the migration script may
and may not infer automatically — critically, **the migration script must
never emit an `ordering` edge it has not independently proven**, which
rules out the "just copy `changes[]` order" shortcut for any of the 47
records needing explicit annotation.

**Selection algorithm.** §2's event down-set enumeration, filtered by
`change_state_at()` applied per-event; §9's two-dimensional
`ErratumSelection` (chronology × per-candidate coverage).

**Implementation mapping strategy.** §4's closed `Coverage` sum type,
keyed by event-set, with the single, formally-defined default
(`UNRESOLVED`) for any reachable-but-unauthored state.

**Validator strategy.** §10's ten invariants, with invariant 6 (the
mechanical overlap check, generalised from a one-time audit into a
standing, per-`validate`-run check) as the single most consequential
addition of this revision — it is what would have caught Sangan before
merge, not after.

**Expected files touched by the eventual implementation:** unchanged list
from §11 (schema, `model.py`, `validate.py`, `lflist.py`, both erratum test
files, plus the 49 records needing explicit annotation — up from 47 in the
file-count sense once the 2 needs-manual-review records are resolved).

### Proposed atomic implementation sequence (revised)

1. **Schema v2 alongside v1**, exactly as the first revision proposed, now
   specified with `events{}` (keyed dict)/`ordering.chains`/`ordering.
   edges`/`states[]` (event-set-keyed) and the `Coverage` sum type. Pure
   schema addition, no `model.py` change, independently reviewable.
2. **Dual-shape parsing into one internal representation** (§8 option D).
   New `selection_at()`/`ErratumSelection`/`HistoricalState` implemented
   against the internal event-down-set structure only. Gated by a v1-vs-v2
   equivalence regression test at every currently-defined snapshot.
3. **Migrate the 236 trivial + 11 genuinely fully-ordered records**, using
   the single-event sugar for the 236 and a migration script that
   **independently re-derives and proves** each `ordering.chains` edge for
   the 11 from their dates directly — never copies `changes[]` position.
   Regression-gated.
4. **Migrate the 47 records needing explicit annotation** (39
   bundled/independent-axis + 8 mechanically-distinct order-unknown, using
   the already-published classifications from the Edison audit and this
   document's corpus re-audit — no new research needed for these 47).
   This commit is expected to *change* the computed candidate set for the
   29-of-38 Edison records already known to be self-contradictory today,
   **and, newly, for Sangan and Witch of the Black Forest at any snapshot
   after their overlap window begins** — verified against
   already-published expectations for the former, and against fresh
   regression tests written specifically for the latter two (§11).
5. **Resolve the 2 needs-manual-review records** (Insect Imitation, Last
   Will) — a human decision on whether their researcher-inferred order
   (§5.6) licenses an `ordering` edge, then migrated per whichever tier is
   chosen.
6. **Switch `validate.py`/`lflist.py` to the new API directly**, remove
   deprecated integer-based compatibility shims. Implement §10's
   invariant 6 (the mechanical overlap check) as a standing validator
   check in this same commit — this is the change that prevents
   regression, not merely documents past instances of it.
7. **Delete v1 schema support.** (D) formally becomes (B).
8. **Retire/rewrite the characterisation tests** pinning known-buggy
   behaviour (`OrderingConstraintTest`, `test_giant_rat_selection_shape`),
   replaced with tests asserting the corrected semantics, **plus new
   tests for Sangan and Witch of the Black Forest specifically** —
   records this document found that the original Edison-scoped
   characterisation tests had no way to know needed covering.

Each step remains independently committable and independently
verifiable as a no-op against every currently-defined format's generated
`dist/` output, except step 4, whose entire point is to correct behaviour
for the now-48 (not 44) already-documented affected records.
