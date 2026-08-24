# Erratum state-model v2 — architecture research (roadmap item 5c follow-on)

**Scope: design only.** No canonical `data/errata/*.json` record changes, no
`retroformats/model.py`/`retroformats/validate.py`/`retroformats/lflist.py`
changes, no generated `dist/` changes, no schema changes committed in this
milestone. This document exists to choose an architecture and prove it
against real records before any implementation work is scheduled.

**Status: architecture FROZEN for implementation.** Four correction
passes (bb2c6a7 → 9b34a79 → 8aa67b2 → 1e1d7c9 → this commit) is enough
adversarial scrutiny for a first implementation attempt to begin. The
historical-event DAG (§2's Architecture 1, as refined) is the accepted
design; its foundational properties are frozen — §13 lists all sixteen,
**untouched by this pass**. This pass corrects the migration SEQUENCE
only (§8, §13): the previously-proposed "normalise v1 and v2 into one
shared representation" transition step is retracted (§8's Giant Rat
counterexample shows it is impossible to satisfy for the 49 structurally
affected records, not merely awkward), replaced by an explicit, temporary
legacy/v2 boundary — this is how an intentionally-buggy legacy data model
coexists with its replacement during migration, not a change to what the
replacement is. No further architecture exploration is expected unless
implementation discovers a concrete counterexample the frozen model
genuinely cannot represent; a found imprecision in a proof, a
migration-spec inconsistency, or a transition-plan flaw (as this and
every prior pass's corrections have been) is grounds for a targeted fix,
not grounds to reopen the choice of architecture.

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
  "chains": [["v1", "v2", "v3", "v4"]],   // sugar for pairwise "v1 before v2 before v3 before v4",
                                          // basis: "date-proven" for every edge in a chain of dated events
  "edges": [
    { "before": "b1", "after": "a2", "basis": "date-proven" },        // chronology alone proves it (§5)
    { "before": "x1", "after": "x2", "basis": "researcher-inference",
      "note": "..." }                                                  // chronology is inconclusive; requires
                                                                        // this explicit justification, or the
                                                                        // validator rejects the edge (§5)
  ]
}
```

`chains` is pure sugar over `edges` — `["v1","v2","v3"]` desugars to
`{before: v1, after: v2}` + `{before: v2, after: v3}`, nothing more; the
`basis` on each desugared edge is computed automatically as
`"date-proven"` whenever §5's PROVEN test passes for that pair (true for
every real chain in this corpus — §7), and the validator rejects the
`chains` sugar outright for a pair it is not proven for, forcing the
author to either use an ad hoc `edges` entry with an explicit `basis`
instead, or leave the pair unordered. There is **no default chain inferred
from `events{}`'s own key order** — a record with four events and no
`ordering` block at all has *zero* declared edges, full stop, regardless
of what order the events happen to be written in the JSON. This is the
direct fix for the defect this whole document exists to close: **omitted
ordering information means no edge, never "the previous item."** Every
declared edge, chain-sugared or ad hoc, must additionally clear §5's
PROVEN/CONTRADICTED/inconclusive test — an edge the dates contradict is a
hard validator error regardless of any claimed `basis`; an edge in the
inconclusive middle zone is rejected unless it carries an explicit,
non-`"date-proven"` basis.

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
map to `coverage.kind == "modern"` and no other state may; every declared
`ordering` edge must pass §5's exact PROVEN/CONTRADICTED test (§10.6) and,
if not PROVEN by dates alone, carry an explicit evidentiary `basis`
(§10.7) — §7's exhaustive corpus re-audit is what finds real,
previously-undetected defects like Sangan's, but that audit is a
migration-time and legacy-v1 tool (§10), not itself a standing v2 runtime
check; the standing v2 checks are the edge-validity invariants themselves.

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
object (one of the 9 Edison cluster records where today's schema's
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
result, and genuinely not self-contradictory there — the revival-timing
erratum (2013-10-11) is still confirmed OLD at Edison (2010-04-24), so
candidate 1's positional claim that it has not occurred is unopposed.

**Corrected by §7's exhaustive audit: this record is nonetheless one of
the 48, at every snapshot from 2013-10-11 onward — including the
"hypothetical 2014-01-01" this section used to illustrate.** This
section's earlier claim that Tyrant Dragon is "not self-contradictory...
because nothing was ever asserted about their relative order" repeated
this document's own central mistake one layer down: the absence of an
asserted order says nothing about whether a *positional* candidate can
still collide with an event's own independently-computed status once one
side becomes determinate. Once the revival-timing erratum is confirmed
NEW, candidate 1 — positionally, "extra-attack occurred, revival-timing
did not" — keeps claiming revival-timing has not occurred, directly
contradicting its own confirmed status; verified directly against live
code. This is the same shape as Sangan (§3.J), just discovered later.

### E. Axe of Despair — the second order-unknown, mechanically-distinct case

Structurally identical to Tyrant Dragon, including the correction just
made: review notes silent rather than explicit about order, which — as
established in the Edison audit and unchanged here — is not evidence of
order either; not self-contradictory at Edison (the functional erratum,
2013-06-28, is still confirmed OLD there), but — corrected here to match
Tyrant Dragon — one of the 48 at every snapshot from 2013-06-28 onward,
for the identical positional reason.

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
**This record is not one of §7's 48** — v1's three candidates (`0, 1, 2`)
are never independently contradicted, since neither event is ever
confirmed old or new — but it is still structurally affected: v1's
array-prefix model can express only three of these four down-sets,
permanently omitting `{summon-rule alone}`. §7 works this out as the
dedicated counterexample distinguishing "48 records with a wrong label"
from "49 records whose migration changes something."

**Corrected classification.** An earlier pass in this research placed
YZ-Tank Dragon in the bundled/independent-axis category, reasoning from
"both differences are encoded in one upstream script" by analogy to Giant
Rat. That analogy does not hold up: the two behaviours here — a
contact-fusion material-zone restriction, and a nomi-vs-semi-nomi
summoning condition — are the *same two questions*, addressing the *same
Cannon-fusion lineage*, as XY-/XYZ-/XZ-Dragon/Tank Cannon (YZ-Tank
Dragon's own siblings, already correctly classified
mechanically-distinct-order-unknown in the Edison audit, because a
material-eligibility question and a re-Summon-restriction question are
substantively unrelated, not two aspects of one ruling). Being encoded in
one upstream script is a fact about *implementation reuse convenience*
upstream, not evidence that the two questions are thematically one — the
same is true of every sibling. YZ-Tank Dragon differs from its siblings
only in being undated on *both* sides rather than one; that is a
chronology fact, not a bundling fact, and does not change which category
it belongs in. Corrected: **mechanically-distinct-order-unknown**, grouped
with its three siblings and the other 5 records in that category (§7).

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
   worded, in the review notes of the vast majority of the 49 records
   found in §7 needing nontrivial migration (including YZ-Tank Dragon's
   own notes — one of the 49, not one of the 48, but disclaiming order
   just as explicitly).
5. **Co-occurrence: two or more transitions belonging to one event** —
   a **first-class chronology fact**, not documentation: it removes real
   candidate states from the down-set space (§2's `policy-revision` worked
   example: 2 states instead of 4). **Corrected in this pass: this is a
   strictly stronger claim than "bundled/shared-package," and the two must
   not be conflated** — an earlier pass in this research suggested the
   two might turn out to be the same thing on further research; they do
   not. "Bundled/shared-package" (§7's migration category, covering all 38
   Edison cluster-1 records) is a *research/thematic* label: these two
   transitions answer aspects of the *same underlying ruling question*,
   and upstream happens to implement both together in one script. That is
   evidence about *subject matter*, not about *timing* — none of it says
   the two transitions happened at the same historical moment, only that
   they are about the same thing. "Co-occurrence" is a *chronology* claim:
   these two transitions are known to have happened together, as one
   historical act. **No record in this corpus currently has evidence
   meeting that bar** — every one of the 38 bundled records' own review
   notes says the two transitions "cannot be sequenced" (order unknown),
   which is evidence of *ignorance about order*, not evidence of
   *simultaneity*. Migrating a bundled record using the co-occurrence
   mechanism would be asserting something the record's own evidence does
   not support. §7's migration procedure is corrected accordingly: **all
   38 bundled records, like the 9 mechanically-distinct records, migrate
   as two separate, unordered events with no declared edge.** **Corrected
   in this follow-up pass: the two categories are not distinguished by
   `axis` either.** `axis` names *one semantic behavioural question per
   transition* — Giant Rat's own worked example (§2) already assigns its
   two bundled transitions two genuinely *different* axis labels
   (`search-reveal-procedure`, `search-activation-legality`), not a
   shared one, precisely because a shared underlying ruling still poses
   two distinct questions. Treating "shared/related axis" as the 38's
   signature and "distinct axis" as the 9's would have been the same
   category error this paragraph exists to correct, one layer down. **The
   bundled-vs-mechanically-distinct split is a research/audit
   classification, useful for this document's own accounting and nothing
   else — it has no representation in canonical v2 data at all**, not
   `axis`, not a new field: no part of the selection algorithm, the
   validator, or the migration script treats the two categories
   differently, so a field encoding the split would carry zero
   computational use, exactly the kind of unused structure this redesign
   exists to avoid. Where the relationship between two transitions is
   worth recording per record, it belongs in that record's own
   `review.notes` prose, as several already do. The co-occurrence
   mechanism remains fully specified (§2) and provably correct (§12) for
   the day evidence like the task's own worked example ("changed in the
   same policy revision, exact date unknown") actually turns up in this
   corpus — it is simply not yet needed by any record audited so far.
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

### The ordering-edge validation rule, worked out precisely

**Corrected in this pass.** An earlier version of this section proposed
rejecting a declared edge `{before: A, after: B}` whenever the two
events' possible-date *intervals overlap* — that is wrong: overlapping
intervals only mean the dates cannot *prove* the edge, not that they
*contradict* it. Sangan (§3.J) is the concrete counter-example the
correction was checked against: its two events' intervals overlap
(2011-02-02..2019-04-03 and 2016-09-15), and the dates genuinely cannot
say which came first — but nothing about that overlap makes "verification
before name-lock" *impossible*, only *unproven*. The corrected rule
distinguishes three cases, not two:

For events A, B, define two derived quantities directly from the fields
already in the schema (`effective.date`+`precision`, or
`old_attested_through`/`new_attested_from`) — no new evidence kind, just a
precise reading of the existing ones:

- `last_confirmed_old(E)`: the latest date at which E is still guaranteed
  not to have happened. For an exactly-dated event (day precision), this
  is the day before the date; for month/year precision, the day before
  the widened interval's start. For a bounded event, this is
  `old_attested_through` directly. `None` (unbounded, arbitrarily far in
  the past) if neither is present.
- `first_confirmed_new(E)`: the earliest date at which E is guaranteed to
  have already happened. For an exactly-dated event, the widened
  interval's end (equal to the date itself at day precision — "on the
  effective date itself the new behaviour applies," per
  `change_state_at()`'s existing, unchanged semantics). For a bounded
  event, `new_attested_from` directly. `None` (unbounded, arbitrarily far
  in the future) if neither is present.

Then, for an asserted edge "A before B":

- **PROVEN** iff `first_confirmed_new(A) <= last_confirmed_old(B)` (both
  defined). Meaning: even in A's *latest* possible scenario and B's
  *earliest* possible scenario, A still precedes B — true under every
  date assignment the evidence allows. Chronology alone is sufficient
  basis; no additional evidence is required, and none of the 11
  genuinely-fully-ordered records (§7) need any.
- **CONTRADICTED** iff `last_confirmed_old(A) >= first_confirmed_new(B)`
  (both defined). Meaning: even in A's *earliest* possible scenario and
  B's *latest* possible scenario, A still does not precede B — impossible
  under every date assignment the evidence allows. A **hard validator
  error**, regardless of what basis an author claims for the edge — dates
  that flatly rule out an order cannot be overridden by an assertion.
- **Otherwise, compatible but inconclusive** (includes every case where
  either quantity is `None`, and Sangan's case where both are defined but
  neither inequality holds). The edge is neither proven nor forbidden by
  chronology alone — **it requires an explicit, authored `basis`** (§5.6's
  researcher-inference tier, or a directly cited source) before the
  validator accepts it; an edge with no basis in this zone is rejected,
  not silently allowed. This is the concrete mechanism behind item 6
  above, generalised from "Insect Imitation/Last Will's specific shape"
  to every edge in this zone.

Verified computationally against the corpus, not merely derived
abstractly: every consecutive pair in all 11 genuinely-fully-ordered
records (§7) is **PROVEN** (confirming the category is correctly named,
not merely "not yet found to be wrong"); Sangan's and Witch of the Black
Forest's single pair, and Giant Rat's, and Tyrant Dragon's, are all
**compatible but inconclusive** under this exact test — never
contradicted, matching every record's own review notes, which assert
"unknown," never "impossible." No record in the corpus currently declares
(or, under this revision's corrected migration procedure, would need to
declare) an edge that chronology contradicts — the CONTRADICTED case is
included here because the validator must reject it if one ever is
authored, not because one exists today.

**The non-negotiable principle, restated and now enforced by construction
rather than by convention:** UNKNOWN must remain UNKNOWN. §4's coverage
rule and this section's ordering rule work together to guarantee it — a
down-set is never excluded from the candidate space without either a
PROVEN or explicitly-evidenced `ordering` edge or a co-occurrence grouping
backing the exclusion, and a candidate's coverage is never silently
anything other than `UNRESOLVED` without an authored entry.

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

## 7. Migration analysis — an exact, exhaustive test, not a sweep

**Corrected twice over in this pass.** The first version of this
document's test was too weak ("does every transition have some dating
information," which missed Sangan). The second version fixed the
*substance* of the test but ran it as a **snapshot sweep** — each
transition's own dates plus a buffer, plus a yearly scan from 2000 to
2030 — which is thorough but not exhaustive, and this document should not
call a sweep "proven" when an exact method is available. It is: each
relevant transition's own status can change at most **twice** as a
function of snapshot date — OLD→AMBIGUOUS (where its uncertainty window
begins) and AMBIGUOUS→NEW (where it ends); day-precision collapses these
to one instant (§12.6). That "two" is the count of status-changing
*boundaries* per transition, not the count of calendar dates the test
below evaluates — evaluating a boundary correctly means checking a
representative point on each side of it, so the concrete date set is
larger before deduplication (corrected below). Because no transition's
status can change *between* two consecutive boundaries by construction,
evaluating the algorithm at a representative point around each boundary,
across the whole record, is a complete, finite case analysis, not a
sample of one.

**The exact test**, run against every one of the 296 records: for each
record, collect every relevant transition's own representative boundary
dates — for an exact date at precision P, the day before *and* the day of
the precision-widened interval's start, and the day before *and* the day
of its end (four raw dates, collapsing toward fewer distinct calendar
dates at day precision, where start and end coincide); for bounded
chronology, the attested-through date and the day after it, and the day
before attested-from and attested-from itself (up to four dates, fewer
when only one bound is present). This is a finite set, **at most `4 ×
(relevant transitions)` raw dates before deduplication** — not `2 ×`,
which this document previously stated: that smaller number is the count
of status-changing boundaries per transition (correct, above), not the
count of calendar dates evaluated around them (double that, before the
usual collapsing from shared dates across a record and day-precision
degeneracy within one transition). This prose correction changes no
result — the 296-record sweep already evaluated the fuller date set in
code; only the earlier paragraph's stated bound was imprecise. At each
date in the deduplicated set, compute `selection_at()`'s
candidates and check every candidate index `k` against every transition's
own, independently-computed status: candidate `k` claims transitions
`0..k-1` have occurred and `k..end` have not; a candidate is
self-contradictory if any transition in the "occurred" set is
independently confirmed OLD, or any in the "not occurred" set is
independently confirmed NEW. Because no transition's status can change
*between* two consecutive boundary dates by construction, checking every
boundary date checks every distinct behaviour the record can ever exhibit,
at any snapshot whatsoever — past, present, or any future format this
project might add.

**Result, re-confirmed exactly: 48 of 296 records, the identical set the
sweep found.** The exact method changes no record's classification
relative to the sweep — it upgrades the finding from "thorough" to
"exhaustive," which matters because this document should not claim
completeness it has not actually verified. The 44 already established by
the Edison audit, plus **Sangan, Witch of the Black Forest** (§3.J — both
events dated, windows overlap) and **Insect Imitation, Last Will** (§3.I).

**"48" is a symptom count, not the exhaustive set of structurally
affected records — the two must not be conflated.** 48 is the exact
count of records that produce a self-contradictory candidate label under
**v1's** linear-chain model at *some* snapshot — a defect symptom that
can only exist where v1's model asserts something and gets it wrong. A
separate, larger set is the exhaustive scope of records whose migration
to v2 is not a pure rename: the **49 records requiring nontrivial,
order-aware migration** under this document's own taxonomy below — 38
bundled/shared-package + 9 mechanically-distinct order-unknown + 2
needs-manual-review, i.e. `296 − 236 trivial − 11 fully-ordered = 49`.
Every one of the 48 falls inside the 49, by construction — self-
contradiction requires an unproven-order pair of relevant changes, which
is exactly the 49's membership condition; the 236 trivial and 11
genuinely-proven-ordered records cannot produce it. Checked exhaustively
against all 49: **all 38 bundled records, 8 of the 9 mechanically-
distinct, and both of the 2 needs-manual-review are in the 48** (`38 + 8
+ 2 = 48`) — the sole exception, at every snapshot, forever, is
**YZ-Tank Dragon**. **This "38 of 38" figure is not in tension with
§3.B's "29 of the 38 Edison records self-contradictory... the other 9
worked by accident": §3.B measures self-contradiction *at the Edison
snapshot specifically* (2010-04-24) — a check this project already
performs — while "48" measures it *exhaustively, at any snapshot,
including many this project has never queried*. A record can pass the
narrower, currently-relevant check and still be one of the 48 at a
snapshot only a future format would reach — Tyrant Dragon and Axe of
Despair (§3.D, §3.E) are worked examples of exactly this, corrected
below.**

**YZ-Tank Dragon, the worked counterexample.** Both of its relevant
changes carry a null `effective.date` and no bounded attestation at all
(§3.H) — `change_state_at()` returns AMBIGUOUS at every snapshot,
forever; neither transition is ever independently *confirmed* old or
new. Verified against live code: `selection_at()` returns
`candidates=(0, 1, 2)` at every checked snapshot, and — confirmed by
running this section's exact boundary test against it specifically — no
candidate is ever flagged self-contradictory, because self-contradiction
requires an independently-confirmed status that disagrees with a
candidate's claim, and no such confirmation is ever possible for this
record. YZ-Tank Dragon correctly, permanently, is not one of the 48.

But v1's three candidates were never the full state space to begin with.
Candidate index `k` under v1's model means "the first `k` entries of
`changes[]`, in array order, have occurred" — a *prefix* of the array.
For two relevant changes that structure admits exactly three subsets —
`{}`, `{first}`, `{first, second}` — and cannot express `{second}` alone,
because array-prefix membership is not the same thing as arbitrary
subset membership, regardless of whether any candidate happens to be
mislabeled. Under the accepted v2 model, YZ-Tank Dragon's two behaviours
— the contact-fusion material-zone restriction, and the nomi-vs-semi-nomi
summoning condition — are two separate, unordered events; the down-set
space over two unordered events is the full power set: `{}`,
`{material-rule}`, `{summon-rule}`, `{material-rule, summon-rule}` — four
states (§3.H already establishes this). Migrating YZ-Tank Dragon to v2
does not just relabel three states correctly — it adds a fourth,
previously-*unrepresentable* state ("summon condition loosened,
material-zone restriction not yet lifted") that v1's array-prefix model
had no way to name at all, self-contradictory or not. A v1-vs-v2
equivalence check that only asks "did any of the 48 stop being
self-contradictory" cannot see this, because YZ-Tank Dragon was never
self-contradictory to begin with — §10 and §13's cutover-check wording
are corrected below to check for it explicitly.

**Corrected taxonomy** — YZ-Tank Dragon reclassified (§3.H): its two
questions (contact-fusion material zone; nomi-vs-semi-nomi condition) are
the same *kind* of pairing as its siblings XY-/XYZ-/XZ-Dragon/Tank Cannon,
already correctly classified mechanically-distinct-order-unknown, not
bundled — being undated on both sides is a chronology fact, not evidence
the two questions are thematically one.

| Category | Records |
|---|---|
| Trivial (0-1 relevant changes) | **236** |
| Genuinely, exactly, exhaustively ordered | **11** |
| Bundled/shared-package (Edison cluster-1 only) | **38** |
| Mechanically-distinct, order-unknown (Edison non-cluster: 6; Sangan, Witch of the Black Forest, YZ-Tank Dragon: 3) | **9** |
| Needs manual review (researcher-inferred order: Insect Imitation, Last Will) | **2** |
| **Total** | **296** — 236 + 11 + 38 + 9 + 2 = 296 |

**The 11 genuinely, exactly ordered records** — every consecutive pair
independently verified **PROVEN** under §5's precise test, not merely
"not found to be contradictory": Blackwing - Sirocco the Dawn, Blue-Eyes
Toon Dragon, Blue-Eyes Ultimate Dragon, Dark Necrofear, Necrovalley, Night
Assailant, Rescue Cat, Soul Rope, Swords of Concealing Light, Toon
Mermaid, Toon Summoned Skull. Ten of these eleven carry only exact,
day-precision dates throughout (§12.6: two exactly-dated events can never
fail PROVEN, by construction — their order is a direct date comparison,
not an inference); the eleventh, Rescue Cat, has one bounded event whose
`new_attested_from` (2008-12-15) precedes its dated sibling's date
(2017-03-30) — `first_confirmed_new(Rescue-Cat-event) <=
last_confirmed_old(dated-sibling)` holds with room to spare, genuinely
PROVEN despite the imprecision, not merely non-overlapping-by-inspection.

**Why exhaustive, not swept, matters for trusting "48":** a sweep can miss
a narrow window between samples; an exact, boundary-only enumeration
cannot, because it is not sampling a continuous space at all — it is
enumerating a genuinely finite one. This section's "48" is now a claim
this document can defend against "did you check *every* possible
snapshot," not just "did you check enough of them."

**Migration procedure, corrected on two points from the prior revision.**
Because omitted ordering means no edge, a migration script cannot copy
`changes[]` order into `ordering.chains` for any record — it must instead
run §5's PROVEN test itself and emit an edge only when that test passes.
Two further corrections from the second revision of this document:

- **The 38 bundled and 9 mechanically-distinct records migrate to
  byte-for-byte-identical JSON *shape* — two separate, unordered events,
  with no `ordering` edge, and no event-merging.** "Bundled" is a
  research label (these two transitions are about the same underlying
  question), not a chronology claim (that they happened together) — §5.5
  corrects this conflation directly, and no record in the corpus has
  evidence meeting the co-occurrence bar. **They are not distinguished by
  `axis` either** (§5.5): each event's transitions carry their own
  accurate, per-question `axis` label regardless of category — the
  bundled-vs-mechanically-distinct split itself has no field in canonical
  v2 data at all, since nothing computational reads it.
- **No edge is emitted anywhere without passing §5's PROVEN test or
  carrying an explicit, authored `basis`.** This applies uniformly:

  - **236 trivial**: single event, no `ordering` possible or meaningful —
    pure, safe rename.
  - **11 fully-ordered**: the migration script emits `ordering.chains`
    only for pairs its own PROVEN check passes — for all 11, this reduces
    to "sort by date, chain the sorted order, `basis: date-proven`
    throughout," since sorting and proving are the same computation here.
  - **38 bundled + 9 mechanically-distinct = 47**: the migration script
    emits **no `ordering` edges at all** (§5's test does not pass for any
    of them — every one is compatible-but-inconclusive); each event's
    `axis` label is transcribed from that transition's own semantic
    question (already documented per-record), not from its
    bundled/mechanically-distinct category, which is not written into the
    record at all — no new research is needed for these 47.
  - **2 needs-manual-review**: blocked on a human §5.6 decision before
    any emission at all — not even the "no edge" default is written
    automatically, since resolving whether their researcher-inferred
    order should become an explicit `basis`-carrying edge is exactly the
    open question.

**Same-date, not-proven-co-occurring events**, per the task's explicit
question: if two events happen to carry the identical exact date without
any co-occurrence evidence, they remain two separate events (never
auto-merged); no `ordering` edge is needed between them (§5.7/§12.6 — §5's
PROVEN test does not actually hold in *either* direction for identical
dates, and none is required, since their independently-computed statuses
can never actually disagree regardless of order); and
their statuses will always move together at every snapshot as a
consequence of sharing a date, not as a consequence of any declared
relationship.

**Do not trust the Edison 44/85 as the entire affected population, and
do not trust the corrected 48 as it either.** Proven exactly, not
swept: the exhaustive check found 4 records entirely outside Edison's
known-wrong/divergence set with the identical self-contradiction defect,
none of which currently produce a *visible* symptom for any
currently-defined format, exactly the risk this document's introduction
describes. But "48" only counts records where v1's model produces a
*wrong* answer it asserts with false confidence — it is silent on
YZ-Tank Dragon, where v1's model was never wrong about any of its three
candidates, only *incomplete*, missing a fourth state it had no way to
represent at all (worked above). The **49** — this document's exhaustive
taxonomy of records needing nontrivial, order-aware migration — is the
count to use for "how many records does this redesign actually change
something about"; **48** remains the right count for "how many records
does today's schema actively mislabel."

---

## 8. Backwards compatibility

**Corrected in this pass: the previous plan — normalise both v1 and v2
data into ONE shared internal representation during migration, selected
by a single algorithm throughout the transition — is retracted. It is
not merely inconvenient, it is impossible to satisfy for the 49
structurally affected records, and attempting it corrupts coverage
mappings for the 236+11 safe ones too if the same code path is trusted
for both.** The end state is unchanged: v2-only, v1 deleted. What changes
is how the project gets there.

**The Giant Rat counterexample, worked precisely.** At Edison
(2010-04-24), Giant Rat's two changes are, by array position,
`changes[0] = verification` (bounded, OLD at Edison) and `changes[1] =
activation-semantics` (undated, AMBIGUOUS forever). v1's positional
algorithm computes `k_min = 0`, `k_max = 1`, `candidates = (0, 1)` —
candidate 0 means `{}` (baseline), candidate 1 means "`changes[0]` has
occurred, `changes[1]` has not" — i.e. **"verification has occurred"**,
positionally, regardless of verification's own independently-computed
status. This is Giant Rat's actual, already-known self-contradiction
(§3.A): candidate 1 claims verification occurred while verification is
independently confirmed OLD (has not occurred) — one of the 48.

Now ask: what does a *correct* event-DAG representation of this record
produce?

- **If `changes[]` array order is translated into a declared edge**
  (`verification -> activation-semantics`, the exact array-order-as-
  evidence move this whole document exists to forbid): a down-set
  respecting that edge can only include `activation-semantics` if it
  also includes `verification`. Verification is confirmed OLD — no valid
  down-set may include it — so, transitively, no valid down-set may
  include `activation-semantics` either. **The only candidate is `{}`.**
- **If the events correctly remain unordered** (§2's actual rule: no
  edge unless proven or sourced, and nothing here is either): both
  `{}` and `{activation-semantics}` are valid down-sets. **This is the
  correct v2 answer.**

Neither of these is v1's `(0, 1)` / `{}, "verification occurred"`. The
first produces a strict subset with no room for the second candidate at
all; the second produces the right *shape* (2 candidates) but a
different *meaning* for the non-empty one — v2's second candidate means
"activation-semantics occurred, verification did not," the semantic
opposite of what v1's candidate 1 (mis)labelled. **There is no
event-down-set translation of this record that reproduces v1's actual
output**, because v1's output is, in a precise sense, not a real
historical state at all — it is a positional label. At any snapshot
before a record's first transition becomes determinate that label
trivially matches reality (`{}` always means "nothing has happened,"
under v1 or v2 alike), but that is not the interesting case: at *some*
snapshot, for 48 of the 49 structurally affected records (§7, Giant Rat
included — its Edison-snapshot contradiction is the concrete case just
worked through), the positional label openly contradicts an
independently-computed event status. Mapping v1's candidate 1 onto v2's
`{activation-semantics}` "to preserve the old implementation slot" would
attach *verification's* authored coverage to a state that is actually
about *activation-semantics alone* — silently corrupting the coverage
mapping the moment it is read back, not merely producing a cosmetically
different candidate set. **Do not do this, for any of the 49.**

**The corrected approach: a hard, explicit, temporary legacy/v2
boundary, not a shared representation.** For as long as both shapes
exist in the corpus (schema v2 exists as of this document; canonical
data does not use it until §13's step 4):

- **A v1-shaped record** is parsed as legacy v1 and selected by the
  existing, unmodified positional algorithm. Its known bugs (the 48,
  and any future finding like §3.D/E's) remain exactly as
  characterised, isolated to records that have not yet migrated, until
  the record in question migrates.
- **A v2-shaped record** is parsed into the frozen historical-event DAG
  (§2) and selected *only* by the semantic event-down-set algorithm
  (§9). No v2 code path ever reads `changes[]` array position as
  evidence of anything.
- **Repository loading may detect which shape a record uses and
  dispatch accordingly** — that is a structural fact about the JSON
  (§2's schema branches are already mutually exclusive by construction,
  §1's implementation), not an inference. It must never *force* a
  v1-shaped record through v2 semantics, or vice versa.
- **No legacy numeric version semantics (`version_index`, integer
  `candidates`) may appear inside `HistoricalState`/`ErratumSelection`**
  (§9) — a consumer needing to bridge the two during the transition uses
  the semantic helper operations §13's revised sequence describes
  (chronology-ambiguous?, modern-possible?, determinate-coverage,
  baseline-selected?, candidate labels/state keys), never a fabricated
  integer standing in for a v2 down-set that has no linear position to
  begin with.

This dual path is acceptable *because* it is temporary, explicit, and
narrow: every v1-shaped record keeps behaving exactly as it does today,
completely unaffected by v2's existence, until the specific commit that
migrates it; every v2-shaped record is understood only on its own,
correct terms from the moment it exists. Nothing is ever asked to be
both at once. §13's revised implementation sequence works out exactly
which commit does what, and §10's revised equivalence-test policy states
precisely what "correct" means at each stage — a blanket "v1 output ==
v2 output" is *false by design* for the 49, so it is never the test.

**49 records, not 247, need an active research step before they can be
migrated at all**, split into two disjoint groups (§7): 47 (38 bundled +
9 mechanically-distinct order-unknown) whose research is *already
done* — the Edison audit's and this document's own corpus re-audit's
classifications are the research, migration only needs to transcribe
them — and a separate 2 (Insect Imitation, Last Will) whose research is
*not yet done at all*, blocked on a human choosing which §5 constraint
tier their researcher-inferred order claim belongs to before any
annotation, mechanical or otherwise, can be written.

---

## 9. Selection API design — chronology and implementation coverage as separate dimensions

**Corrected.** The first version of this document's `ErratumSelection.
outcome: "determinate" | "ambiguous" | "gap" | "modern"` mixed two
independent questions — is the *chronology* determinate, and what
*coverage* does each candidate have — into one enum, which cannot cleanly
represent the task's own posed mixed case (ambiguous chronology, one
candidate implemented, one a known gap). Split into two dimensions:

**Corrected in this pass: no identity (`is`) comparison, and no reliance
on the dataclass's default whole-object equality either.** The first
version of this API used `self.candidates[0] is self.modern_state` and
`self.modern_state in self.candidates` — both fragile, because
`HistoricalState` is a plain `@dataclass(frozen=True)`, whose generated
`__eq__` compares *every* field (`events`, `label`, `coverage`), not just
the event-set that actually identifies which state something is. Two
`HistoricalState` objects built independently (e.g. one from `candidates`,
one as `modern_state`, on separate code paths) could carry the same
`events` but a differently-worded `label`, and would then compare unequal
under the default `__eq__` even though they represent the *same* state —
exactly the kind of bug this whole document exists to stop tolerating,
just relocated from the schema into the API. **A state's identity is its
event-set, nothing else** — every comparison below is written against
`.events` explicitly, never against a whole `HistoricalState`:

```python
@dataclass(frozen=True)
class HistoricalState:
    events: frozenset[str]           # THE identity of a state — every comparison uses this field only
    label: str                       # human-readable, descriptive only — never compared
    coverage: ImplementationCoverage # §4 — descriptive only — never compared

@dataclass(frozen=True)
class ErratumSelection:
    chronology: str                          # "determinate" | "ambiguous" -- ONLY this dimension
    candidates: tuple[HistoricalState, ...]   # always the full plausible set; len == 1 iff determinate
    modern_state: HistoricalState             # the terminal state, for "is modern among candidates"

    @property
    def is_modern(self) -> bool:
        return (self.chronology == "determinate"
                and self.candidates[0].events == self.modern_state.events)

    @property
    def modern_is_possible(self) -> bool:
        return any(c.events == self.modern_state.events for c in self.candidates)

    @property
    def has_known_gap(self) -> bool:
        return any(c.coverage.kind is Coverage.KNOWN_GAP for c in self.candidates)

    @property
    def needs_implementation_research(self) -> bool:
        return any(c.coverage.kind is Coverage.UNRESOLVED for c in self.candidates)
```

Audited the rest of this document's API surface for the same class of
mistake: §10's validator invariants (state-key uniqueness, unreachable
states, the all-events/modern check) are all specified in terms of
event-sets directly, not `HistoricalState` object comparisons, so they do
not have this problem; §4's completeness rule keys `states[]` lookups by
event-set from the start. This API section was the one place a
whole-object comparison had crept in, now corrected.

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

**Corrected in this pass: the previous revision's invariant 6 (a
permanent, standing "self-contradictory candidate" sweep, re-run on every
`validate` invocation) is retired as a v2 invariant.** On reflection it is
mostly tautological for v2 data: the down-set enumeration algorithm (§2)
is *defined* so that a candidate is only ever generated if every included
event is NEW-or-AMBIGUOUS and every excluded event is OLD-or-AMBIGUOUS —
a v2 record, correctly parsed by a correctly-implemented algorithm,
*cannot* produce a self-contradictory candidate, the same way a correctly
implemented sort cannot return an unsorted list. Re-checking this on every
record at every `validate` run would mostly be re-verifying the
algorithm's own implementation once per record, which is what software
tests are for, not what per-record data validation is for. What actually
prevents "the next Sangan" in v2 is **not** a runtime sweep — it is the
combination of (a) no implicit ordering (an author cannot accidentally
assert an edge), (b) every explicit edge passing §5's PROVEN/CONTRADICTED
test, and (c) candidates being generated from live per-event status, not
from a stale positional label. The sweep's real, still-valuable uses are
named explicitly below, in their own scoped subsection after the ten
invariants, rather than smuggled in as a redundant v2 correctness check.

Ten invariants:

1. **Every `ordering` reference names a real event id.**
2. **No cycles in `chains`/`edges`** — standard topological sort;
   **declaration order of events plays no role in validity** — an
   `ordering` entry may reference an event declared anywhere in
   `events{}`, forward or backward, and cycle detection is the only thing
   that can reject a set of edges.
3. **Every `states[]` entry is a down-set the ordering/co-occurrence graph
   can actually produce.**
4. **No duplicate state keys.**
5. **The all-events state is unambiguously `coverage.kind == MODERN`, and
   no other state may be** — per §4's named exception, this holds whether
   or not an author writes an entry for it.
6. **CORRECTED: every declared `ordering` edge must pass §5's exact
   PROVEN/CONTRADICTED test, not the earlier (wrong) "intervals don't
   overlap" test.** An edge the dates **CONTRADICT** —
   `last_confirmed_old(A) >= first_confirmed_new(B)` for a declared
   `before: A, after: B` — is a hard error unconditionally; overlapping
   intervals alone (Sangan's shape) are explicitly **not** grounds for
   rejection, only for requiring (7) below. This replaces, and corrects
   the mathematics of, the previous revision's invariant 7.
7. **Every edge not PROVEN by dates alone must carry an explicit
   `basis`** (§5.6, §5's ordering-edge section) — `"date-proven"` is
   asserted automatically only when §5's PROVEN test actually passes;
   anything in the compatible-but-inconclusive zone with no `basis`, or
   with `basis: "date-proven"` claimed falsely, is rejected. This is the
   validator-enforced form of §5's "requires an explicit, authored basis"
   rule, and is the actual, positive mechanism (not a sweep) that keeps
   an unevidenced edge out of the corpus.
8. **Unreachable state mappings are detected** — a `states[]` entry whose
   down-set the ordering/co-occurrence graph can never actually produce
   (dead data, most likely a typo or a stale edit) is flagged.
9. **Ambiguity cannot silently fall back unless policy explicitly allows
   it** — unchanged in principle from today's `format.erratum-ambiguous`/
   `unresolved_policy` handling, operating over `ErratumSelection.
   candidates` (§9) instead of integers.
10. **Co-occurrence claims require sources** — an `events{}` entry with
    2+ transitions must cite `sources` supporting the co-occurrence claim
    specifically, not merely sources for each transition's own content.

**The sweep is not deleted from this project's toolkit — it is
re-scoped, explicitly, to three uses that are not "a standing v2
invariant":**

- **A one-time (or as-needed) legacy-v1 audit tool** — exactly what §7
  used to find the 48 affected records and prove the 11 safe ones exactly,
  run against `changes[]`-shaped data specifically to decide which records
  can be mechanically chain-migrated and which need a human.
- **A regression-test fixture** — `OrderingConstraintTest` and
  `test_giant_rat_selection_shape` (§11) pin the *old*, known-buggy v1
  behaviour precisely so a future change to the (deleted, post-migration)
  v1 code path cannot silently regress it further before removal.
- **A v1-vs-v2 equivalence/cutover check** — during migration (§8, §13).
  **Corrected in this pass: this is NOT a blanket "v1 output == v2
  output for every record" assertion — that is false by design for the
  49 (§8's Giant Rat counterexample proves it, not merely suggests it).**
  Three distinct guarantees, not one, cover the whole corpus at every
  point in the migration:

  - **(A) While a record is still v1-shaped, its output stays exactly
    legacy-compatible.** Not "equivalent to v2" — there is no v2 output
    to compare against for a record that has not migrated. The legacy
    positional algorithm runs unmodified, bugs and all, for exactly as
    long as the record has not migrated (§8). This is the standing
    guarantee that holds continuously through the whole transition, not
    a one-time migration-commit check.
  - **(B) For the 247 mechanically-safe migrations (236 trivial + 11
    genuinely proven-ordered), v1 and v2 semantics must be equivalent**
    at every checked snapshot — these are precisely the records §7
    proved v1's array position already matched real evidenced order for,
    so a v2 record built from the same evidence must compute the
    identical candidate/state at every snapshot v1 did. Any divergence
    here is a real migration bug, not an expected difference.
  - **(C) For the 49 nontrivial migrations, differences are expected and
    must be asserted explicitly, not merely tolerated:**
    - the 48 legacy self-contradiction symptoms disappear, where the
      record's own change_state_at() would have made them visible — no
      v2 candidate for these records is ever mislabeled the way their
      v1 output was;
    - **YZ-Tank Dragon specifically gains the previously-unrepresentable
      fourth state** its v1 array-prefix model could never express, even
      though it was never one of the 48 to begin with (§7's worked
      counterexample);
    - every one of the 47 already-classified unordered records exposes
      the **full** correct reachable state set — every
      structurally-reachable down-set, not merely the subset v1's
      array-prefix model could name;
    - no *additional*, unexpected difference is produced beyond these —
      a migration that changes something this list does not name is a
      bug to investigate, not a difference to wave through.

  **This check must never be phrased as "changes behaviour for exactly
  the 48" — 49 records (§7) are expected to change in some way, and one
  of them was never part of the 48 at all.**

None of these three is "run on every future `validate` call against live
v2 data" — that role belongs to invariants 6 and 7 above, which do the
actual, positive work of keeping bad edges out, rather than re-deriving
that the algorithm implements its own specification correctly.

---

## 11. Build impact (traced, not modified)

Unchanged in file list from the first version of this document, updated
in *what changes per file* to reflect the event/transition split and the
sum-type coverage:

| File | What would change |
|---|---|
| `schemas/erratum.schema.json` | New `events{}` (keyed dict, not array — an alternative to `changes[]`, not a replacement of it yet), each with `effective` + `transitions[]` (no per-transition chronology); new `ordering.chains`/`ordering.edges`; new `states[]` keyed by event-id-sets with the `Coverage` sum type (§4). **Done (f01fc11) — `changes[]`/`implementation` remain fully valid and untouched alongside the new shape** for as long as any v1-shaped record exists (§8); deleted only at §13's final step, once none does. |
| `retroformats/model.py` | **Corrected in this pass: additive, not a replacement, until §13's final deletion step.** `Erratum.relevant_changes()`/`implementation_for_version()`/`selection_at()` (the legacy positional algorithm) are left exactly as they are; a new, separate event-down-set enumeration + state lookup (§2, §9) is implemented alongside them, used only for v2-shaped records. `change_state_at()` is reused by both — its OLD/AMBIGUOUS/NEW semantics are unchanged by this whole redesign, only what it is applied to (a bare v1 change vs. a v2 event's `effective` block) differs. Only §13's final step deletes the v1 path, once it has nothing left to select for. |
| `retroformats/validate.py` | **Corrected in this pass: a temporary, explicit dual branch (§13 step 3), not a replacement, until §13's final deletion step.** New checks for §10's invariants 6/7 (the PROVEN/CONTRADICTED edge test, the evidentiary-basis requirement) apply to every v2 ordering constraint — **both literal `ordering.edges` entries and every `ordering.chains`-desugared pair** (§2's sugar is exactly that, sugar over edges, not a way to bypass the same proof burden) — wired in once `model.py`'s v2 path exists (before any v2 record actually lands, so the first real one is checked by the real invariants from day one); the existing v1 ordering check is untouched and keeps running for v1-shaped records. `format.erratum-include-wrong-version`/`-redundant` and similar consumers branch explicitly on which shape a record has — an integer check for v1, an event-set-equality check for v2 — never a fabricated integer standing in for a v2 state. The legacy self-contradictory-candidate sweep (§10) ships as a migration/audit utility, never a `validate.py` runtime path for v2 data. Only §13's final step removes the v1 branch and the integer-based compatibility shims. |
| `retroformats/lflist.py` | Smallest-touched of the three code files, as in the first version of this document — same explicit, temporary dual-branch treatment as `validate.py`: `select_applicable_errata()` and `baseline_override()`/`parity_override()` branch on shape, using `.version_index`/`.candidates` for v1 and `.chronology`/`.candidates[0].coverage` for v2, never mixing the two inside one code path. `parity_override()`'s "walk in order, take first usable" logic needs a defined canonical walk order over v2 states for a non-chain record (recommendation unchanged: fewest events applied first, ties broken by event id — degenerates to today's behaviour for every genuine chain). Only §13's final step removes the v1 branch. |
| Importers | Unaffected — no importer currently generates multi-event records. |
| Report output (`cli.py` `report -v`) | Cosmetic — prints state labels instead of version integers. |
| Tests | `OrderingConstraintTest` and `test_giant_rat_selection_shape` rewritten against corrected semantics (unchanged conclusion from the first revision) — plus **new** regression tests for Sangan and Witch of the Black Forest specifically, since those two were not previously known to need one. |
| Existing JSON records | Per §7 (corrected): 247 records (236 trivial + 11 genuinely, exactly ordered) migrate via a script that **proves** each `ordering.chains` edge it emits rather than copying `changes[]` position; a separate 47 records (38 bundled + 9 mechanically-distinct order-unknown) migrate as unordered event pairs with no `ordering` edge — the bundled-vs-mechanically-distinct split stays a research classification recorded in this document, not a field in canonical data — all already researched (Edison audit + this document's own corpus re-audit — no new research needed for these 47); a further, disjoint 2 records (Insect Imitation, Last Will) are not yet researched at all and are blocked on a human §5.6 decision before any annotation can be written. |
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
for identical dates), so no `ordering` edge is *required* for correctness.
Checked against §5's exact test (not just asserted): **neither direction
is PROVEN** here — `first_confirmed_new(A)` (2015-06-01) is *not*
`<= last_confirmed_old(B)` (2015-05-31) in either direction, since same-day
events give each other no room to be strictly before one another — nor is
either direction CONTRADICTED. This is the correct, expected answer: dates
identical to the day cannot establish which (if either) came first within
that day, and the record does not need them to, since — as established
above — their statuses can never disagree regardless of order. An earlier
draft of this stress case incorrectly claimed an edge here would be
trivially PROVEN; corrected on review of the arithmetic. This is
different from declaring them one *event*: two same-dated-but-separate
events still, in principle, permit a future finding that they were not
actually simultaneous (a day-precision date is not a certificate of
atomicity) — merging them into one event is a stronger, evidentially
distinct claim (§5.7), and this stress case confirms the model does not
force that stronger claim just because the dates happen to match.

**7. Cosmetic changes interspersed with behavioural ones.**
**CORRECTED (a114ee3) — the original text below was wrong about the
implemented runtime and is retained struck through, because the difference
is load-bearing for migration.**

> ~~Unaffected — `kind in {functional, ruling}` filtering happens
> per-transition, before any transition's parent event enters the down-set
> machinery; an event containing only cosmetic/engine transitions never
> creates a distinguishable state, identical in effect to today's
> filtering.~~

The correct rule, and the one `ErratumV2.selection_at()` implements:

> **ALL historical events participate in chronology and order consistency.
> ONLY functional/ruling events survive the projection into
> implementation-state identity.**

Filtering happens *after* down-set reasoning, not before it. A
cosmetic/engine-only event still happened-or-didn't at a snapshot, and
through the ordering DAG that fact can force a relevant predecessor to have
occurred (a confirmed-NEW successor requires every predecessor, relevant or
not) or forbid a relevant successor (a confirmed-OLD predecessor forbids
every successor) — even though the event itself never appears in any
`HistoricalState`'s identity. Reachable down-sets are computed over the FULL
event set, projected onto relevant ids only at the end, and deduplicated so
an undetermined cosmetic event cannot fork one real implementation state
into several identical-looking candidates.

This is observable, not theoretical:
`tests/test_migration_audit.py::AuditSensitivityTest` exhibits a record where
a cosmetic event's confirmed-NEW status collapses an otherwise ambiguous
relevant event to a single determinate state — v1 says `ambiguous`, v2 says
`modern`.

It does **not** destabilise migration, for a reason that had to be proved
rather than assumed: a *date-proven* ordering edge can never add a constraint
the two events' own statuses already impose, and migration emits no other
kind of edge. See `erratum-v2-migration-audit.md`, and
`ProvenEdgesAddNoConstraintTest` for the exhaustive check.

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

**Mitigating the extra nesting for the common case (180 of 296 records —
re-derived; see `erratum-v2-migration-audit.md`):** a single-event,
single-transition record whose transition is FUNCTIONAL or RULING may use
flattened sugar. Two corrections to the figure once written here:

- it is **180**, not 247. Under full-event semantics *every* change becomes
  an event, so a record with one relevant change and a cosmetic change
  beside it has two events and cannot use single-event sugar (35 such
  records), and 21 records have no relevant change at all;
- cosmetic/engine-only records **cannot** use this shape. Their
  relevant-event set is empty, so `{}` IS the terminal state and its coverage
  is unconditionally `modern` — which `authoredBaselineCoverage` rightly
  forbids. There is no baseline state for `coverage` to describe. Those
  records use full v2 with no authored `states[]`.

The sugar shape:

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

**Migration strategy.** **Corrected in this pass (§8): NOT a "normalise
into one shared representation" plan.** A hard, explicit, temporary
legacy/v2 boundary instead — a v1-shaped record is parsed and selected
exclusively by the unmodified legacy algorithm until the specific commit
that migrates it; a v2-shaped record is parsed and selected exclusively
by the semantic event-down-set algorithm from the moment it exists;
nothing is ever asked to be both. §7's corrected, per-category proof
burden still governs what a migration script may and may not infer
automatically — critically, **the migration script must never emit an
`ordering` edge it has not independently proven**, which rules out the
"just copy `changes[]` order" shortcut for any of the 47 records needing
explicit annotation.

**Selection algorithm.** §2's event down-set enumeration, filtered by
`change_state_at()` applied per-event; §9's two-dimensional
`ErratumSelection` (chronology × per-candidate coverage). This is the
v2-only algorithm — during the transition it runs *alongside* the
unmodified v1 positional algorithm (§8), never in place of it for a
still-v1 record, and the two are never merged into one code path.

**Implementation mapping strategy.** §4's closed `Coverage` sum type,
keyed by event-set, with the single, formally-defined default
(`UNRESOLVED`) for any reachable-but-unauthored state.

**Validator strategy.** §10's ten invariants, with invariants 6 and 7 (the
exact PROVEN/CONTRADICTED edge test, and the evidentiary-basis requirement
for anything not PROVEN) as the two that actually keep bad edges out of
v2 data going forward — the exhaustive sweep that *found* Sangan (§7)
remains a legacy-v1 migration and audit tool, not a standing v2 check
(§10), since a correctly-implemented v2 algorithm cannot generate a
self-contradictory candidate by construction.

**Expected files touched by the eventual implementation:** unchanged list
from §11 (schema, `model.py`, `validate.py`, `lflist.py`, both erratum test
files, plus the 49 records needing explicit annotation — up from 47 in the
file-count sense once the 2 needs-manual-review records are resolved) —
**corrected in this pass: `model.py`/`validate.py`/`lflist.py` are each
touched twice, not once** — first additively (the new sequence's steps
2–3, standing up the v2 path beside the untouched v1 one), then
subtractively (step 7, once every record has migrated and the v1 path
has nothing left to select for).

### Proposed atomic implementation sequence (corrected in this pass — replaces the "dual-shape parsing into one representation" step, which was not merely awkward but impossible to satisfy for the 49 structurally affected records; §8's Giant Rat counterexample)

1. **Schema v2 alongside v1** (§13 step 1). **Done — `f01fc11`.** Pure
   schema addition, no `model.py` change, independently reviewable.
2. **Implement the v2 semantic model/parser/selector ALONGSIDE the
   existing v1 model/selector — not merged with it.** `HistoricalEvent`,
   behavioural transitions, ordering-graph down-set enumeration,
   `Coverage`/`ImplementationCoverage`, `HistoricalState`, the semantic
   `ErratumSelection` (§2, §4, §9) — all new code, all reachable only
   for v2-shaped records. **Existing v1 `selection_at()` behaviour is
   unchanged, byte for byte.** `Repository` loading may detect a
   record's shape structurally and dispatch to the matching parser, but
   must never force a v1-shaped record through v2 semantics or vice
   versa. No canonical records migrated yet; no `validate.py`/`lflist.py`
   consumer switched over yet. Independently testable against the new
   code path in isolation (no live v2 data exists to exercise it against
   yet, so this step's own tests construct synthetic v2 fixtures).
3. **Introduce the temporary consumer compatibility layer** —
   `validate.py`, `lflist.py`, and any reporting code branch explicitly
   and narrowly on record shape, so both a legacy v1 selection and a
   semantic v2 selection can be consumed correctly side by side. **Never
   fabricate a `version_index` for a non-linear v2 state** to satisfy an
   integer-shaped consumer — prefer the semantic helper operations this
   layer needs directly (chronology ambiguous?, modern possible?,
   determinate coverage, baseline selected?, candidate labels/state
   keys) over forcing both representations into one fake shared
   structure. Wire §10's invariants 6 and 7 (the PROVEN/CONTRADICTED
   edge test, the evidentiary-`basis` requirement) into `validate.py`
   here too, so the very first v2 record step 4 lands is already
   checked by the real invariants, not merely accepted by schema alone.
   **With no canonical v2 records yet, this commit must preserve every
   currently-generated `dist/` output exactly.**
4. **Migrate the 247 mechanically-equivalent records — re-derived and
   RE-CONFIRMED exactly by `erratum-v2-migration-audit.md` after a
   comparator bug in that audit's first pass was found and fixed (the bug
   produced a false 296-of-296 claim; the corrected comparator reproduces
   this document's own 247/49/48/236/11 figures exactly, independently
   re-derived rather than assumed).**

   **The representation blocker is LIFTED; canonical migration itself has
   STILL not begun.** Two independent representation gaps held this step
   back: v1 implementation metadata with no v2 coverage destination at all
   (`status` on all 296 records, `tested` on 240, `gap.upstream_checked`/
   `gap.behavioural_impact` on 53 each, one bare `reason` — demonstrably
   STATE-SPECIFIC, since a change's `resulting_implementation` can and does
   carry a different `status` than the record's baseline `implementation`
   — see `erratum-v2-migration-audit.md`'s worked Blue-Eyes Toon Dragon
   example), and the 11 parity-only records' identity (below). Both are
   now designed AND implemented — `implementation_metadata[]` (keyed by
   relevant-event down-set, orthogonal to `Coverage`) and
   `reference_identities[]` (record-level, orthogonal to `Coverage`,
   `reference_id`-keyed) — with a corrected schema, runtime, validator, and
   consumer precedence rule, and this project's own migration-audit tooling
   independently verifies every one of the 247 semantically-equivalent
   records' v1 metadata/identity round-trips into them (`metadata_
   unrepresented_count == 0`, `parity_only_unrepresented_count == 0`). See
   `docs/research/erratum-v2-representation-gaps.md` for the full design
   record. **This step still has not begun**: implementing the
   representation is a prerequisite, not the migration itself — starting
   step 4 for real remains a separate, later decision.

   The shape split, once migration begins, is finer than "single-
   event sugar for the 236" — under full-event semantics every change is an
   event, so only **180** of the 236 trivial records have exactly one event
   in total and can use sugar; **35** have one relevant change with a
   cosmetic/engine sibling event and need full v2 with no `ordering`; the
   remaining **11** are the genuinely, exactly ordered multi-event records,
   migrated via a script that **independently re-derives and proves** each
   `ordering.chains` edge from their dates directly, never copies
   `changes[]` position. Regression-gated on guarantee B holding for every
   one of the 247 — `tests/migration_audit.py` derives this figure from the
   runtime on every test run, rather than asserting it. **11 of the 247 are
   parity-only identity records** (zero relevant events, a usable
   historical passcode from period-text-only reference divergence):
   equivalence alone was never sufficiency, and these 11 proved it —
   migrating them as ordinary `states[]` coverage would have silently
   discarded the identity GOAT's `reference_parity` depends on, since v2's
   terminal state always synthesises MODERN coverage. **No longer
   excluded**: `reference_identities[]` (orthogonal to `Coverage`,
   `reference_id`-keyed) now represents exactly this fact, implemented and
   independently verified to round-trip all 11 records' identities exactly
   (`docs/research/erratum-v2-representation-gaps.md`). They migrate
   alongside the rest of this step, not as a separate future one, once
   step 4 actually begins. The **10 pure cosmetic/engine, no-historical-
   state records** also belong in this step's full accounting (180 + 35 +
   11 + 11 + 10 = 247) — an earlier pass's migration-sequencing text
   omitted them; they carry no behavioural identity to preserve, only
   `implementation_metadata[]` for whatever workflow fields they have.
5. **Migrate the 47 already-researched unordered records** (38
   bundled/shared-package + 9 mechanically-distinct order-unknown) as
   separate, unordered events — no `ordering` edge for either group; the
   bundled-vs-mechanically-distinct split is a research classification
   recorded in this document, not a field in the migrated JSON; no new
   research needed, using the already-published classifications from
   the Edison audit and this document's own corpus re-audit. **This is
   where corrected semantic behaviour intentionally lands** (§10's
   guarantee C): the computed candidate set changes for the 29-of-38
   Edison records already known to be self-contradictory today, and,
   newly, for Sangan and Witch of the Black Forest at any snapshot after
   their overlap window begins — verified against already-published
   expectations for the former, fresh regression tests for the latter
   two (§11). **YZ-Tank Dragon gains its fourth, previously-
   unrepresentable state** here too, despite never having been one of
   the 48 (§7's worked counterexample) — the equivalence check (§10)
   must assert this explicitly, not only check the 48 for a resolved
   symptom.
6. **Resolve and migrate the 2 needs-manual-review records** (Insect
   Imitation, Last Will) — a human decision on whether their
   researcher-inferred order (§5.6) licenses an `ordering` edge, then
   migrated per whichever tier is chosen.
7. **Delete: the legacy v1 selector; the v1 parser/normalisation path;
   the temporary consumer branches step 3 introduced; the v1 schema
   branch.** Only at this point does the project genuinely have one
   internal representation and one selection algorithm — because, and
   only because, every canonical record is v2-shaped by now. Deleting
   this earlier, per §8, is exactly the move that corrupts coverage
   mappings for records not yet migrated.
8. **Retire/rewrite the characterisation tests** pinning known-buggy
   legacy behaviour (`OrderingConstraintTest`, `test_giant_rat_selection_
   shape`), leaving the permanent v2 semantic regression suite in their
   place — plus new tests for Sangan and Witch of the Black Forest
   specifically, records this document found that the original
   Edison-scoped characterisation tests had no way to know needed
   covering.

**The invariant every decomposition of this sequence must preserve, even
if the exact commit boundaries above are refined later: no canonical
unordered v2 record may land before consumers can understand semantic
event-set selections** — i.e. step 3 (or its equivalent) must exist and
land before step 5 (or its equivalent) does, in every ordering of this
work. Each step remains independently committable and independently
verifiable as a no-op against every currently-defined format's generated
`dist/` output, except steps 5 and 6, whose entire point is to correct or
complete the computed candidate/state set for the 49 records they touch.
Step 5's 47-record scope (38 bundled + 9 mechanically-distinct) resolves
the self-contradiction symptom for 46 of the 48 — every one except
Insect Imitation and Last Will, the 2 needs-manual-review records outside
its scope, resolved only once step 6 annotates them — and, separately,
gives YZ-Tank Dragon (never one of the 48) the state its v1
representation could never express at all (§7).

---

### Frozen for implementation

The historical-event DAG architecture is **frozen**. The following
properties are the accepted design and are not to be redesigned absent a
concrete, implementation-discovered counterexample the frozen model
cannot represent — a wrong proof, an imprecise bound, a misclassified
record, or (this pass) a transition-plan flaw in how legacy v1 data
coexists with v2 during migration (as every correction across this
document's four passes has been) is fixed in place, not treated as
grounds to reopen the architecture choice. **This list is unchanged by
this pass — the correction was to §8/§13's migration sequence, not to
any property below:**

- events are chronology nodes;
- one event may contain multiple transitions only for sourced
  co-occurrence;
- transitions carry semantic behaviour, not chronology;
- event declaration order has zero meaning;
- omitted ordering means no edge;
- ordering edges are explicit;
- date-PROVEN edges need no extra basis;
- chronology-CONTRADICTED edges are forbidden;
- compatible/inconclusive edges require an explicit evidentiary basis;
- behavioural axis is semantic metadata only;
- state identity = event-set;
- state implementation coverage is the six-way sum type;
- terminal all-events state = MODERN;
- unauthored reachable non-terminal state = UNRESOLVED;
- chronology and coverage remain separate API dimensions;
- UNKNOWN != GUESS.

The proposed eight-step atomic implementation sequence above is the
accepted next step.
