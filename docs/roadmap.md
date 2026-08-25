# Roadmap

Accuracy before breadth: a format is only "supported" when its data validates, its
sources are cited, and its generated assets are regression-tested. The order below
reflects that.

## Phase 1 — harden the two proof-of-concept formats

1. ~~**Date the errata corpus.**~~ **Done (2026-08-20).** The corpus is now a
   reviewed, source-backed, date-aware dataset: 296 records (211 imported + 85
   found by sweeping the Edison-legal pool), every one reviewed, classified
   155 ruling / 120 functional / 21 cosmetic, with 113 exact dates, 58 bounded
   chronologies and 125 explicitly unresolved. GOAT's 211-entry include list is
   gone (one sourced parity policy, parity unchanged) and Edison computes 72
   historical implementations from evidence alone. See docs/errata.md.
   Follow-ups below (1a-1e).

   1a. **Chronology for the undated era rulings.** 125 records are unresolved,
   almost all undated era *rulings* carried by upstream GOAT scripts —
   damage-step activation windows, miss-timing registration, trigger
   registration. Konami never announced these per card, so they need period
   rulings documents (UDE Judge's List archives, Metagame.com judge columns,
   per-set rulings PDFs). Each one resolved shrinks Edison's
   `unresolved_policy` fallback.
   1b. **Close the search-verification interval.** The old state is attested
   through 2011-02-02 and the modern policy from 2019-04-03; no announcement of
   the change was found. Narrowing this would firm up a large group of records
   at once (both GOAT and Edison already sit determinately in the old era).
   1c. **The 48 acknowledged implementation gaps** — period behaviours nothing
   upstream reproduces. Each is a candidate for roadmap item 7 (`custom-script`
   generation) once a reserved passcode range is chosen.
   1d. **Contribute back upstream.** 21 cards where our chronology says GOAT
   should use a historical version but Project Ignis's list leaves them modern
   (`format.parity-omits-historical`), plus the cases where its variant is
   behaviourally identical to the modern card (`upstream-variant-cosmetic`).

   1e. **Card identity: TCG-versus-OCG entries.** Mind Master (96782886) is in
   the Edison pool but BabelCDB scopes it OCG-only (`ot=1`) and ships the TCG
   version as a *separate* entry (96782896, `ot=2`, aliased). Our release data
   maps its TDGS-EN016 printing to the canonical code, so the pool references
   a card EDOPro would reject in an official-cards room. This is a card-identity
   question, not errata chronology: it needs a general rule for choosing the
   region-correct implementation of a canonical card.
   `tests/test_repo_data.py::test_pool_cards_are_tcg_scoped_in_the_card_database`
   pins the invariant with this single documented exception.
2. **Cross-check the April 2005 banlist.** The GOAT banlist is currently derived from
   Ignis's whitelist counts. Transcribe the published April 2005 TCG list (Yugipedia
   `April 2005 Lists (TCG)`) with the existing importer, reconcile, upgrade
   `completeness` to `complete`/`verified`, and document any deliberate GOAT-community
   deviations if found.
3. **Verify March 2010 against the Konami archive snapshot** (Internet Archive was
   unreachable this session); upgrade the banlist to `verified`.
4. ~~**Materialise the Edison pool.**~~ **Done (2026-08-19).** `data/releases/`
   covers TCG 2002–2010 (369 products / 8,445 printings, Yugipedia per-territory
   dates + YGOPRODeck printings), Edison materialises to 3,673 cards with every
   boundary case explicitly resolved and sourced, the generated lflist is a full
   `$whitelist`, and regression tests lock cardinality + sixteen edge cases.
   See docs/releases.md. Follow-ups now tracked below (4a–4c).

   4a. ~~Upgrade boundary release events to `verified`~~ **Done (2026-08-20).**
   All five Edison boundary products (plus the TSHD Sneak Peek and both new EU
   dates) are now curated records verified against archived 2010 Konami product
   pages with explicit Tournament Legal Date fields.
   4b. **Per-artwork printing dates** (far-alias alternate arts like Arkana Dark
   Magician are currently absent from cutoff pools unless force-included; audit
   which mattered in-period and encode them).
   4c. ~~Duel Terminal ruling dossier~~ **Done (2026-08-20).** Period policy
   recovered: DT machine exclusives were illegal in sanctioned play (2009-2010
   event FAQs, Konami's 2010-03-19 article, the June 2010 WCQ FAQ's card list);
   the pool exclusion is now primary-sourced.
   4d. **Coverage certification shipped (2026-08-20):** the gap ledger
   (data/releases/gaps.json) makes "complete" coverage an earned invariant -
   all 45 importer-detected anomalies audited (1 roster recovered and imported,
   the rest proven harmless with evidence, mechanically recomputed where
   checkable). Future importer runs that surface new anomalies fail validation
   until the ledger accounts for them.
5. ~~**Edison rules review.**~~ **Done (2026-08-21, corrected 2026-08-21).** Every
   GOAT-composite flag was independently checked against period Konami rulebooks
   (2008/2010/2011 editions, bracketing Edison) rather than assumed from GOAT or from
   EdisonFormat.com's naming. One flag is confirmed necessary and added, backed by a
   period source and an engine test that fails without it: `DUEL_0_ATK_DESTROYED` (the
   0-ATK tie exception wasn't added to the rulebook until Version 7.2, packaged with
   Structure Deck: Dragunity Legion, ~10.5 months after Edison). A second candidate,
   `DUEL_TCG_FAST_EFFECT_IGNITION`, was initially added on the same pass but **removed
   again after an adversarial re-review** (see 5b below) found it overreaches - it is
   tracked as an engine-level known gap instead, not approximated. Four more flags were
   confirmed *not* needed — the modern ocgcore default already matches 2010 TCG play, so
   adding them would have imported behaviour Edison never had:
   `DUEL_6_STEP_BATLLE_STEP`/`DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP`,
   `DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET`, `DUEL_STORE_ATTACK_REPLAYS`. The profile
   (`data/rule-profiles/tcg-mr1-edison.json`) is now a custom 7-flag combination rather
   than a bare `DUEL_MODE_MR1` alias. See `docs/research/edison-rules.md` for the full
   evidence table, the adversarial review, and the correction record. Follow-ups below
   (5a, 5b).

   5a. **SEGOC ordering remains unresolved.** The period-primary Official Rulebook
   (stable 2008-2011) describes a simple two-tier simultaneous-trigger order with no
   mandatory/optional split and no trigger-order tiebreak, directly contradicting
   EdisonFormat.com's claimed four-tier structure, which is traceable only to a 2012
   forum thread (not a period document). `DUEL_TCG_SEGOC_NONPUBLIC` and
   `DUEL_TCG_SEGOC_FIRSTTRIGGER` are left out of the profile pending better evidence —
   candidate lead: an unlocated Konami rulebook edition between v8.0 (Nov 2011) and v10
   (2017) that may be where the stricter structure actually entered print. Three smaller
   flags (`DUEL_USE_TRAPS_IN_NEW_CHAIN`, `DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE`,
   `DUEL_CAN_REPOS_IF_NON_SUMPLAYER`) are similarly left unresolved in `known_gaps` for
   lack of any period source in either direction.

   5b. **Ignition Effect Priority is an engine-level gap, not a flag choice.**
   Reopened, adversarial research (eight independently-dated 2009-2010 period community
   rulings threads from the same forum, corroborated by a Konami OCG FAQ ruling for
   Destiny HERO - Malicious)
   found the 2010 TCG rule was a hybrid neither existing flag reproduces: the immediate
   "activate an Ignition Effect as Chain Link 1" window was gated to a **Summon that
   doesn't itself start a chain**, unrestricted by **location**. `DUEL_OCG_OBSOLETE_IGNITION`
   is too narrow on location (Monster Zone only); `DUEL_TCG_FAST_EFFECT_IGNITION` is
   correctly unrestricted on location but too broad on the gate (it also fires after any
   non-Summon chain-end, which period evidence says Edison did not have). Proven
   empirically by a 4-scenario engine test matrix
   (`tests/engine/test_historical_behaviour.py::IgnitionPriorityMatrixTest`). Reproducing
   the historical rule exactly would need a small ygopro-core change decoupling the
   existing flag's two currently-coupled axes into independent settings - not implemented
   here, per the task's scope; see `docs/research/edison-rules.md` row 1 for the exact
   change that would be needed.

   5c. ~~**Card-behaviour triage.**~~ **Done (2026-08-22, audit only; corrected
   three times, 2026-08-22, after successive adversarial reviews).**
   Recomputed Edison's two headline errata-warning counts from HEAD rather than
   trusting a remembered figure — 44 `format.erratum-modern-known-wrong` + 41
   `format.erratum-known-divergence` (not 48; "48" is the project-wide count of
   `implementation.strategy: "unresolved"` records, 7 of which don't apply at Edison's
   exact snapshot) = 85 unique cards, zero overlap, zero requiring a D
   (identity/engine-issue) classification — these counts are unaffected by any
   correction below. An initial A/B/C/D partition (A 44 / B 41 / C 0) used too weak a
   test for A ("at least one candidate implemented" instead of "every
   historically-plausible candidate implemented"). Corrected partition: **A 0 / B 41
   (unchanged) / C 44 / D 0**, verified by live recomputation against every record in
   the 296-record corpus, not just the 44. **Within the 44, two structurally different
   kinds of C were found and must not be conflated, and neither is a validated chain**:
   38 records (the entire failed-search/deck-verification cluster) are **bundled
   independent-axis** cases — two behavioural axes bundled in one upstream GOAT
   script, which every one of their own review notes says cannot be sequenced against
   each other, and for which no implementation exists for the state where only one
   axis has changed. The other 6 (Axe of Despair, Tyrant Dragon, Vampire Lord,
   XY-/XYZ-/XZ- Dragon/Tank Cannon) were first (wrongly) folded into that same
   independent-axis bucket, then (also wrongly, on a later correction pass) called
   "ordinary linear chains" on the theory that `changes[]` list order established
   their relative sequence — but list order is not evidence, and a direct per-record
   audit found **zero of the six have an evidenced relative order**: four say outright
   "cannot be sequenced... because it has no chronology at all"; the other two simply
   never address it. Their candidate sets only look non-contradictory at the Edison
   snapshot because the dated member of each pair (2013 or 2016) is independently
   confirmed not-yet-happened by its own date, regardless of any relationship to the
   undated member — recomputed at a snapshot after that date, all six reproduce the
   identical self-contradictory-candidate symptom Giant Rat shows at Edison. Corrected
   taxonomy: **38 bundled/independent-axis + 6 order-uncertain/mechanically-distinct +
   0 genuinely order-evidenced chains among the 44 C records** (the 41 B-partition/
   divergence records are this corpus's genuinely order-evidenced chains — every
   relevant change in each carries a real, specific date). It is not true that
   resolving chronology alone is guaranteed to finish the 38 bundled cases: whichever
   way the undated
   activation-semantics axis resolves, the *direction* of any needed follow-up custom
   script is to **add** a modern-style valid-target-exists check at activation (the
   existing baseline script has none) while *retaining* old-era reveal-on-whiff
   behaviour for resolution-time whiffs — the reverse of what an earlier pass described.
   That undated axis falls under roadmap item **1a** (undated era rulings), not 1b (the
   companion verification-axis interval, which is already resolved old at Edison and
   not the open question for this cluster).
   The underlying `Erratum.selection_at()` candidate computation was also found not to
   propagate a change's definite state to its chain neighbours (a real gap against the
   schema's "ordered oldest-to-newest" contract) for 2 of 4 possible two-change
   orderings — deliberately left unpatched, since propagation is safe only where order
   is genuinely evidenced (the 41 B records) and wrong for all 44 C records, bundled
   and order-uncertain alike, and the code cannot currently tell evidenced order from
   no evidence either way. A further, deeper finding: even the *meaning* of a given
   candidate index depends on `changes[]` list order, which is inconsistent across the
   38 bundled records — 29 list the dated axis first (producing a self-contradictory
   candidate 1 that asserts an already-ruled-out state, with the true intermediate
   state unrepresented by any index) and 9 list the undated axis first (producing a
   valid candidate 1). Regression tests pin the current (characterization-only, not
   correctness-asserting) behaviour. A data-model fix is proposed, not implemented, in
   `docs/research/edison-behaviour-gaps.md` — scoped as a set of representational
   requirements (ordered chains, unordered/independent axes, order-unknown transition
   pairs, joint states, per-state implementation/gap coverage) rather than a single
   chosen schema; an earlier pass's `order: chained|independent` two-value sketch
   undersold the problem, since ordering is a relation between transitions, not a
   per-change property, and Paladin of White Dragon alone has three relevant changes
   spanning both a bundled pair and a separate order-uncertain one. The 41 B-partition
   cards (unaffected by any correction) cluster more finely (once-per-turn/name-lock 9,
   target-legality 8,
   a nomi-to-semi-nomi wording pattern ~7 and a Union-condition pattern 2 within a
   12-card "other shared ruling-era change" group, plus smaller/bespoke groups) and feed
   directly into item 7 below once that infrastructure exists. A systematic audit of all
   85 rows' generated qualitative fields against their canonical erratum records found
   and corrected 9 further synthesis errors (directional inversions, unsupported
   chronology claims, and one internal self-contradiction). Full per-card inventory,
   clustering, corrected partition reasoning, and both prioritisation views:
   `docs/research/edison-behaviour-gaps.md`. No card behaviour or selection logic
   changed — audit only, per this milestone's scope. **Recommended next step (not
   started): design and implement a representation for ordered chains, unordered axes,
   and order-unknown transitions — beginning with an architecture/design comparison,
   not an assumed schema — before spending a research pass on any chronology question
   this audit surfaced** — the data model cannot yet correctly record the answer for
   any of the 44 C-partition cases at every snapshot (29 of the 38 bundled cases fail
   already at Edison; the rest fail only at later snapshots this audit did not
   evaluate), so chronology research is premature until that representation gap
   closes; see `docs/research/edison-behaviour-gaps.md`'s "Recommended next milestone"
   for the full requirements list.

   5d. ~~**Erratum state-model architecture research.**~~ **Done (2026-08-22, design
   only — no implementation; corrected four times after successive adversarial
   reviews — round 1 found four architecture-level defects, round 2 found the
   ordering-edge contradiction test's mathematics were wrong, the migration-time
   invariant was tautological under the corrected model, one record was misclassified,
   "bundled" and "co-occurrence" were being conflated, ordering edges needed an
   evidentiary basis, and the API used fragile object-identity comparisons; round 3
   found that the "48 self-contradictory records" count was being silently conflated
   with "all records needing nontrivial migration" (YZ-Tank Dragon needs migration but
   was never self-contradictory — it is undated on both sides, so v1 never
   independently confirms either behaviour, only *omits* a fourth reachable state its
   array-prefix model has no way to name), that "bundled/shared-package" was being
   encoded as a shared `axis` label when axis is per-question and both of Giant Rat's
   own bundled transitions already carry distinct labels, that the boundary-count bound
   in §7's exact test understated itself by half, and — surfaced by round 3's own
   adversarial re-verification of its "48 = 38 + 8 + 2" arithmetic — that two worked
   examples (Tyrant Dragon, Axe of Despair) had been carrying a real, older bug since an
   early pass: both were described as "not self-contradictory" on the reasoning that no
   order had been asserted, the exact conflation this whole document exists to fix;
   checked directly, both *are* self-contradictory from their functional erratum's
   effective date onward, corrected in place; round 4 found the proposed migration
   SEQUENCE itself was broken, not the architecture — the plan to normalise v1 and v2
   into one shared internal representation during migration is impossible to satisfy for
   the 49 structurally affected records (Giant Rat at Edison worked precisely: v1's
   positional candidate 1 means "verification occurred" regardless of verification's own
   OLD status; translating `changes[]` order into a declared edge collapses the candidate
   set to `{}` alone, while correctly leaving the events unordered gives the right shape
   but a different, non-corresponding candidate; neither reproduces v1's actual,
   already-known-buggy output) — corrected to an explicit, temporary legacy/v2 boundary
   instead: a v1-shaped record is parsed and selected only by the untouched legacy
   algorithm until the specific commit that migrates it, a v2-shaped record only by the
   semantic algorithm from the moment it exists, and the two are never merged into one
   code path or one equivalence claim — all fixed below, and the architecture itself
   (sixteen frozen properties, untouched by round 4) remains frozen for implementation.**
   Chose and
   proved a replacement for
   `changes[]`'s linear version-chain model: a **historical-event DAG** — events (not
   bare transitions) carry chronology and an explicit, evidence-only partial order
   (`ordering.chains`/`ordering.edges`; omitted ordering means NO constraint, never a
   default chain to the previous entry — the first pass's proposed default was itself
   an instance of the exact array-order-as-evidence bug this research exists to fix,
   and was retracted), each event bundling one or more behavioural transitions so that
   genuine co-occurrence ("A and B changed together, exact date unknown") is
   representable directly rather than reconstructed from same-date coincidence.
   Implementation coverage is a closed six-way sum type (modern / reuse-upstream /
   custom-script / none-needed / known-gap / unresolved), keyed by event-set, with
   exactly one formally-defined meaning for an unauthored-but-reachable state
   (`unresolved`) — never a bare `None`. "Behavioural axis" is corrected to a purely
   semantic label, decoupled from the ordering graph (the first pass's "axis = maximal
   chain" definition was a real conflation, not a stylistic issue). Proved against 10
   real records, including Giant Rat, Paladin of White Dragon (3 events, mixed
   relationships), YZ-Tank Dragon (both events completely undated, its own review notes
   admitting `changes[]` order was chosen "for continuity" — first-party proof this
   project has already made the mistake this research exists to prevent), and
   Insect Imitation/Last Will (a researcher-asserted, undated order claim). Re-running
   the migration audit with an **exact, exhaustive** test (evaluated at every relevant
   transition's own chronology-boundary date — a finite, complete case analysis, not a
   sample — superseding an earlier sweep-based version of the same check) confirms
   exactly **48 records, not 44**, produce a self-contradictory candidate label at some
   snapshot — Sangan and Witch of the Black Forest, both previously misclassified as
   safely "fully-ordered" because every one of their changes carries *some* dating
   information, in fact overlap in exactly the way that reproduces Edison's defect at
   snapshots no currently-defined format queries; verified live-code-exact, not merely
   reasoned about. The ordering-edge validator rule is worked out precisely: an edge is
   PROVEN when chronology alone guarantees it under every possible date assignment,
   CONTRADICTED (hard error) when chronology rules it out under every assignment, and
   otherwise merely compatible-but-inconclusive (Sangan's shape) — which requires an
   explicit, authored evidentiary basis before the validator accepts it, never silent
   inference from overlapping intervals. Migration scope for the full 296-record corpus:
   236 trivial + 11 genuinely, exactly-proven-ordered records migrate via a script that
   proves each edge from dates directly (never by copying list order); a *reclassified*
   38 bundled/shared-package + 9 mechanically-distinct order-unknown (YZ-Tank Dragon
   moved from bundled to mechanically-distinct — its two questions are the same *kind*
   of unrelated pairing as its three Cannon-lineage siblings, not evidence of one
   bundled ruling) + 2 needs-manual-review records need explicit annotation — and,
   critically, "bundled" and "co-occurrence" are corrected to no longer be conflated:
   bundled records migrate as two separate, unordered events exactly like
   mechanically-distinct ones, never merged into one event, since no record in the
   corpus has evidence of genuine simultaneity, only of a shared subject — and the two
   categories are not distinguished by `axis` either, since axis names one semantic
   question per transition regardless of category; the bundled/mechanically-distinct
   split is a research classification with no field in canonical v2 data at all, since
   nothing computational reads it. "48" (the self-contradiction symptom count) and "49"
   (38 + 9 + 2, the exhaustive count of records needing nontrivial, order-aware
   migration) are corrected to no longer be conflated either: 48 ⊊ 49, and the one
   member of 49 not in 48 is YZ-Tank Dragon, worked out as the counterexample. Full
   design,
   three compared architectures (the third, axis-as-mandatory-grouping, is shown to
   collapse into "the first architecture plus a redundant layer" once the axis
   conflation is corrected), adversarial stress-testing (11 cases, including the
   two-valued chained/independent marker's retraction on two independent grounds), and
   the proposed 8-step atomic implementation sequence: `docs/research/
   erratum-state-model-v2.md`. No canonical data, `model.py`/`validate.py`/`lflist.py`, or
   generated output changed in this design-research milestone — design only, per this
   milestone's explicit scope. **The architecture is now frozen** (sixteen named
   properties, listed at the document's end) — no further redesign is expected absent a
   concrete counterexample discovered during implementation. The corrected 8-step
   implementation sequence has since begun as a natural continuation:

   - **Step 1 — schema v2 alongside v1: done** (`bec589c`, corrected `f01fc11` — added
     co-occurrence evidence sourcing, sourced ordering-edge tiers, a real per-kind
     `Coverage` sum type, and a dependency-free schema test suite). Later corrected again
     so the flattened sugar shape accepts only a FUNCTIONAL or RULING transition: a
     cosmetic/engine-only record has no implementation-relevant event, so `{}` is its
     terminal state and its coverage is unconditionally `modern`, which the sugar's
     required baseline coverage rightly forbids — the shape was schema-valid but had no
     consistent runtime meaning. Those records use full v2 with no authored `states[]`.
   - **Step 2 — v2 semantic model/parser/selector: done, and corrected** (`9557708`,
     corrected `a114ee3`). The correction matters for everything downstream: ALL events
     participate in chronology and order consistency, and only functional/ruling events
     survive the projection into implementation-state identity. Cosmetic/engine events
     are *not* filtered before down-set reasoning, as the design document originally
     claimed; that passage is now marked corrected in place.
   - **Step 3 — consumer/validator compatibility: implemented** (`842f84f`), with a
     pre-migration hardening pass on top (`5f7d2da`): historical-identity fail-safety (a
     coverage claiming a substitution without a passcode can no longer reach `int(None)`,
     and a direct `build` refuses cleanly instead of depending on the validator having
     run), explicit v2 include/exclude semantics per coverage kind, ambiguous-selection
     include/exclude diagnostics, and five production-validator holes the JSON Schema
     states but `Repository.load()` never enforced. **That pass's own migration-audit
     tool had a comparator bug** (it reduced a v2 candidate to `len(candidate.events)`
     and compared that integer, silently equating differently-identified states of equal
     size — e.g. Giant Rat's `{verification}` vs `{activation}`), producing a false
     296-of-296 equivalence claim. **Corrected in a follow-up pass**: the comparator now
     does a genuine set comparison of (event-identity, coverage-signature) pairs, and
     the corrected result exactly reproduces this document's own frozen §3/§7 figures —
     247 equivalent, 49 not equivalent, 48 self-contradictory, 236 trivial, 11 fully
     ordered, all independently re-derived, not assumed.
     **A second, narrower hardening pass then corrected four remaining gaps**: the
     candidate construction was silently dropping `script` (optional-but-allowed on
     `reuse-upstream` coverage; affected all 242 reuse-upstream implementations, not
     only the task's Giant Rat example) until a new, construction-independent
     `_coverage_preserved()` check closed it, alongside an honest inventory of v1
     implementation metadata with no v2 destination at all (`status`, `tested`,
     `gap.upstream_checked`, `gap.behavioural_impact`); `_is_valid_passcode()` was
     coercive (`int(value)`) rather than matching this project's own schema semantics
     (`isinstance(v, int) and not isinstance(v, bool)` — rejecting numeric strings,
     bools, and non-integral floats), now pinned against `tests/schema_check.py`'s own
     type matcher; the migration-data comparator collapsed `reuse-upstream`/
     `custom-script` and different `known-gap` reasons into shared signatures, now
     kind-distinct; and the 49 not-equivalent records were labelled uniformly
     `manual-review-blocker`, now correctly split into 47 already-researched
     (design doc §7's taxonomy) and 2 genuinely needing human review (Insect
     Imitation, Last Will, named by the document itself).
     **A third pass then corrected three narrow remaining holes and researched
     (without implementing) two representation gaps**: `if hist:`-style truthiness
     checks let a PRESENT-but-invalid `historical_passcode: 0` silently skip the
     malformed-passcode check in both v1 and v2 validation paths (fixed by testing
     `hist is None` instead); `historical_identity()`'s documented "backstop" still
     called `int(...)`, so a caller bypassing `_usable()`/`_usable_v2()` could still
     coerce `"123"` into a valid-looking passcode (fixed to use the same strict
     `_is_valid_passcode()` authority, zero coercion); and `metadata_inventory()`'s
     `record_count` was actually counting IMPLEMENTATION-OBJECT occurrences (312 for
     `status`, from 296 baseline + 16 `resulting_implementation` objects across only
     296 distinct records), now reported as separate occurrence/unique-record counts
     with a baseline-vs-resulting breakdown that proves several fields (`status` for
     6 records, `tested` for 1) are genuinely state-specific — see
     `docs/research/erratum-v2-representation-gaps.md` for the full design research
     into representing both this metadata and parity-only identity, and the
     terminology correction below.
     **A fourth pass then IMPLEMENTED both representation gaps** — schema, runtime,
     validator, and consumer changes, plus a fix to the metadata-inventory occurrence
     accounting that the third pass's own fix had not fully closed
     (`resulting_implementation_occurrence_count` was itself counting distinct
     records, not occurrences, and a record's later `resulting_implementation` was
     silently overwriting an earlier one before any divergence comparison ran — hiding
     `erratum-swords-of-concealing-light`'s genuine `status` divergence entirely; the
     corrected count is 7 state-specific records, not 6). The reference-identity
     design was corrected before implementation: keyed by a new `reference_id` field
     (WHICH reference list), not solely by `provenance_source` (WHERE an assertion is
     sourced from — a source can host more than one reference list). Full detail,
     including the frozen consumer precedence and every schema/runtime/validator
     change, in `docs/research/erratum-v2-representation-gaps.md`.
   - **Canonical migration of the 247 equivalent records — COMPLETE** (commit
     immediately after `1937239d9fd0ebfb47dc850f298c11c3a60679b0`, the approved
     final pre-migration gate). `data/errata/` now holds **247 `ErratumV2`
     records** (180 flattened sugar + 67 full-v2: 35 single-relevant-with-
     nonrelevant-siblings + 11 fully-ordered multi-relevant + 11 parity-only-
     identity + 10 pure cosmetic/engine) **and 49 `Erratum` (v1) records.**
     **247 migrated successfully to v2; 49 intentionally remain v1** because
     migrating them is NOT semantics-preserving under the legacy positional
     model (v1's positional model and v2's real chronology disagree at some
     boundary for each of the 49 — order-aware migration, not a rename; 47
     already researched, 2 needing manual review: `erratum-insect-imitation`,
     `erratum-last-will`). This is not "all errata migrated," and is never
     described that way while the 49 stand.

     The migration used the already-reviewed dry-run materializer
     (`tests/migration_materializer.py`) verbatim — no manual rewriting, no
     re-derived logic. Verified before and after writing: GOAT output
     byte-identical (hash `0x28E9FC02`, `IGNIS_GOAT_MAP_HASH`), Edison output
     byte-identical, `dist/` byte-identical, live repository validates with
     zero errors, the 49 untouched records byte-identical to their
     pre-migration form (sha256-verified), and the validator warning delta is
     exactly the one legitimate representation change
     (`erratum.no-behavioural-change-with-override: 11 -> 0`, superseded by
     `reference_identities[]` on exactly the 11 parity-only records).
     `docs/research/erratum-v2-migration-manifest.json` records provenance
     (id/path/shape/sha256) for all 247, generated from the live repository,
     never hand-maintained. The full design/implementation/verification
     history — the representation-gap work, the two review-driven correction
     passes, the shadow-migration gate, and the two narrow final corrections
     (porting `erratum.functional-none-needed` to v2; fixing top-level
     `notes`/`applicable_formats_note` preservation from truthiness to key
     presence) — is preserved as historical evidence in
     `docs/research/erratum-v2-migration-audit.md` (frozen pre-migration
     snapshot: `erratum-v2-migration-audit-pre-migration.json`; live
     post-migration audit, now correctly scoped to the 49 remaining v1
     records: `erratum-v2-migration-audit.json`) and
     `docs/research/erratum-v2-representation-gaps.md`.

     **Next milestone**: the explicit/order-aware migration of the remaining
     49, beginning with the 47 already-researched records and separately
     resolving the 2 manual cases — not started, not attempted in the
     migration commit that closed the 247.

## Phase 2 — framework completeness

6. **Deck-level validation tool**: check a `.ydk` against a format (pool + banlist +
   forbidden types + deck sizes) — gives players/tournament organisers a CLI check and
   gives tests a realistic fixture surface.
7. **cdb/script generation for `custom-script` errata**: when we need a historical
   card Ignis doesn't ship, generate `dist/databases/retro-<format>.cdb` rows
   (`alias` → modern, `ot=8`, our own reserved code range — pick one that cannot
   collide with 5047xxxxx/511YYYXXX/prerelease ranges and document it) plus script
   stubs, following the upstream blueprint in docs/research/ignis-goat.md.
8. **Ship as an EDOPro repo**: add a documented `user_configs.json` snippet +
   versioned release layout so `dist/` is consumable directly; test in a real client.
9. **CI**: GitHub Actions running validate + build --check + unittest (workflow file
   already included); add a link-checker for source URLs.
10. **Importer for Format Library formats list** (after maintainer contact): seed
    `formats/` skeletons for the ~90 catalogued formats with `implementation_status:
    missing`, so coverage is visible and contributors can pick tasks up.

## Phase 3 — more formats, by informativeness

11. A second whitelist-era format adjacent to GOAT (e.g. 2005-09) to prove banlist
    sharing and chronology links.
12. A Synchro-era chain (Tengu/Plant 2011) to exercise MR1-vs-MR2-era profile
    boundaries (TCG September 2011 list).
13. HAT (2014) — MR3, pool via releases; Dragon Ruler (2013) — errata-heavy.
14. Early-era formats (Yugi/Kaiba, Critter) — these stress the releases dataset
    (2002-2003) and pre-Advanced-format rules; expect new `known_gaps`.

## Upstream conversations worth having

- **Project Ignis**: the duplicated `511000868` line in GOAT.lflist.conf (cosmetic,
  but it makes the file's runtime hash differ from its entry set); whether they'd
  take an Edison whitelist/pre-errata contributions upstream; whether goat-entries
  conventions (5047xxxxx, ot=8) can be documented in the BabelCDB README.
- **EDOPro (edo9300)**: a mechanism for a repo/lflist to *suggest* duel flags & deck
  sizes for a list (today presets are compiled in; historical formats need manual
  host setup) — even an advisory `#rules:` comment convention would help lobbies.
- **Format Library (Daniel McNelis)**: API usage terms for bulk import; Sets/Prints
  export. On errata specifically, the question is now sharper than "is the table
  populated": the repository's `erratas` table has no reader or writer anywhere in
  the codebase, while the period card texts that DO exist live per printing in
  `Print.description` and are deliberately excluded from the card API response.
  Worth asking whether those per-print texts could be exposed, and what the
  unused Errata model's `effectiveDate`/`expirationDate` were intended to mean.
  Details in `data/sources.json` (`formatlibrary-source`).

## Engine-level regression testing

~~long-term~~ **Shipped (2026-08-20).** `tests/engine/` drives the real ocgcore
(OCG API 11) through ctypes with the pinned BabelCDB card data and CardScripts,
building board states with the core's own `Debug.*` API. Eight tests assert era
*gameplay*, each pairing a historical implementation against the modern one:
Sangan's failed-search Deck reveal, Sangan's and Rescue Cat's post-errata hard
once-per-turn, and Imperial Order's optional-versus-forced maintenance. See
docs/engine-testing.md.

Next steps, in value order:

- **Coverage.** Four implementations across three records are behaviourally
  tested; 234 reuse upstream implementations that are not. Prioritise the cards
  Edison actually substitutes.
- **Untested behaviour classes.** Damage-step activation legality (the largest
  single group of unresolved era rulings — a scenario reaching the Battle Phase
  would let those records be verified as well as dated), equip survival when
  the target leaves, and miss-timing/`EFFECT_FLAG_DELAY` trigger registration.
- **CI.** The engine tests skip without `RETROFORMATS_OCGCORE`, keeping the main
  suite stdlib-only. A separate CI job could fetch DeltaBagooska's
  `libocgcore.so` and the pinned checkouts to run them on Linux.
- **A 64-bit Windows core.** DeltaBagooska ships only a 32-bit `ocgcore.dll`, so
  Windows contributors must use WSL today.
