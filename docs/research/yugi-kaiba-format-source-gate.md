# Early OCG format source and implementation gate

Status: research gate only. This document does not create an early OCG
format, banlist, card pool, or rule profile.

## Verdict

The requested `1999-05-yugi-kaiba` target is not a defensible canonical name
or date. “Yugi-Kaiba” is the community name for the first TCG-era format in
May 2002, built from Starter Deck Yugi, Starter Deck Kaiba, and Legend of
Blue-Eyes. In Japan in 1999, the Yugi and Kaiba products were June 1
`LIMITED EDITION` packs, not the later TCG Starter Decks.

The historically coherent early OCG target is the **Tokyo Dome 1999**
snapshot:

| Field | Research recommendation |
| --- | --- |
| Working id | `1999-08-tokyo-dome` |
| Display name | `Tokyo Dome Format` |
| Format region | `OCG` |
| Release territory | `ocg-jp` |
| Pool cutoff | `1999-08-25` inclusive, to exclude products released on the event date |
| Defining event | Duel Monsters II / `決闘者伝説 in TOKYO DOME`, August 26, 1999 |
| Banlist | July 1999 three-card limited reconstruction, still source-disputed |
| Next conventional format | `Exodia`, community convention, April 10, 2000 |

This is a research recommendation, not approval to add canonical files. The
target is **representable with format-local approximations**, but it is **not
ready for canonicalization**. The remaining blockers are historical source
adjudication and OCG release/card identity coverage, not a required schema
redesign.

## Why the name and date changed

Konami's Japanese card database places the first products in February and
March 1999, then Vol.2, Booster 2, Vol.3, the June 1 Yugi/Kaiba/Joey limited
packs, Booster 3, Vol.4, and later August products. The same database dates
the Tokyo Dome attendee/prize products and Booster 4/Premium Pack material to
August 26. A cutoff on August 25 therefore gives a reproducible pre-event
pool while retaining the conventional Tokyo Dome date.

The February 21 event in the product chronology was a Game Boy national
tournament attendee promotion, not an equivalent early OCG paper-card
championship snapshot. Tokyo Dome is the first practical competitive OCG
anchor in this research scope.

Format Library's API independently calls the conventional record “Tokyo
Dome”, dates it `1999-08-25`, categorizes it as OCG, and points to Exodia as
the next format. That is useful community convention evidence, not primary
historical authority.

## Rules evidence

The translated transcription of the first Japanese Starter Box rulebook is
the period rules evidence available in this repository's research packet,
but it is a later transcription of period material rather than an original
scan. It records 8,000 LP, a minimum-40-card deck with no upper bound, a 10-card
side deck, a five-card opening hand, one draw per turn, no first-turn draw,
no first-turn attack, no hand limit, and Battle inside Main with post-battle
Main actions until End Phase. It also records the
early deck-out rule: when a player cannot draw, the player with more LP wins.

The same rulebook describes one monster, one Spell, and one Trap per turn,
early battle calculations, a single Field Card, and Fusion materials on the
field. Later Expert Rules material is secondary and reports that the Expert
Rules introduced tribute requirements for Level 5+ monsters, allowed multiple
Spell/Trap activations, and allowed Fusion materials from the hand. A strong
secondary reconstruction dates Expert Rules to May 5, 1999 and says official
tournaments used them, but its primary publication source has not been
located. Expert Rules are therefore likely at Tokyo Dome, not proven for that
event; do not silently merge the two rulesets.

The repository can express the numeric limits and most timing toggles. It
cannot reproduce the early damage procedure or “higher LP wins” deck-out
result with an existing pinned ocgcore flag. Those are documented
`known_gaps`, not silently replaced by modern behaviour. Modern chain,
Spell-Speed, priority, and timing semantics also cannot be assumed to have
been present in this early ruleset merely because current ocgcore has them.

## Card-pool and banlist gate

The official product chronology supports an OCG-Japan release-cutoff pool,
but the current repository has 411 release products and zero `ocg*` release
events. A community singleton cross-check contains 370 card identities; 249
are currently in the card index and 121 are absent. That cross-check is not a
substitute for a product-by-product OCG ledger.

The commonly reconstructed July 1999 list limits Dark Hole, Raigeki, and
Trap Hole, with no Forbidden or Semi-Limited section. Sources disagree about
whether this list was broadly effective in July or was effectively a Tokyo
Dome event list. The first implementation must preserve that uncertainty in
the packet and resolve it with a dated primary or contemporaneous source
before creating `data/banlists/ocg-1999-07.json`.

## Frozen errata audit

Every one of the repository's 296 frozen errata records is V2. Evaluating
them at `1999-08-25` using `ocg-jp` territory scope produces this accounting:

| Audit dimension | Count |
| --- | ---: |
| Total V2 records | 296 |
| Determinate chronology | 146 |
| Determinate modern state | 21 |
| Determinate historical states with `reuse-upstream` coverage | 79 |
| Determinate historical states with `known-gap` coverage | 42 |
| Determinate `none-needed` states | 4 |
| Ambiguous chronology | 150 |
| Ambiguous records where modern remains possible | 104 |
| Ambiguous records where modern is known impossible | 46 |
| Ambiguous candidate occurrences | 302 |
| Ambiguous candidate occurrences with `reuse-upstream` | 144 |
| Ambiguous candidate occurrences with `unresolved` coverage | 47 |
| Ambiguous candidate occurrences with `known-gap` coverage | 7 |
| Ambiguous candidate occurrences with modern coverage | 104 |

The number 47 is explicitly two measurements: 47 unresolved candidate-state
occurrences and 47 distinct erratum records containing at least one unresolved
candidate in this corpus. The equality is mechanically asserted; the concepts
are not conflated. The packet carries the exact sorted 46 modern-impossible
IDs, exact sorted 47 unresolved-record IDs, all 79 determinate historical
substitution rows, and their deterministic SHA-256 digest. The substitutions
are a research artifact, not a canonical policy. Modern fallback would leave
150 ambiguous records approximated, including 46 where modern is known
impossible. These are global corpus counts; the incomplete OCG ledger means
they are not claims about every card in the provisional pool.

An explicit modern unresolved policy would select 79 determinate historical
substitutions and leave the 150 ambiguous records on modern only as a
documented approximation. That policy cannot certify the format: 46 of those
ambiguous records have no historically valid modern possibility, and 47
records contain unresolved candidate coverage. No early-format overrides are
therefore proposed by this gate.

## Architecture decision

### B. EXISTING ARCHITECTURE SUFFICIENT WITH DOCUMENTED HOST/ENGINE APPROXIMATIONS

No runtime or schema change is required for this research gate, but the
current structures store host-enforceable approximations rather than literal
unbounded historical maxima. Existing structures can describe:

- `OCG` format region plus `ocg-jp` territory scope and a dated release-cutoff
  pool;
- historical Main `[40, null]`, Side `[10, 10]`, and Extra `[0, null]` as
  research facts, with host approximation Main `[40, 999]`, Side `[10, 10]`,
  and Extra `[0, 999]`; `999` is not historical infinity;
- an explicit historical banlist record once its date and scope are resolved;
- a custom rule profile with documented flags and `known_gaps`;
- fail-safe V2 errata selection that keeps ambiguity visible.

An explicit nullable/unbounded schema maximum would be desirable, but is not
required under the repository's current host-configuration design. The next
implementation may add OCG product/card data and format-local research
artifacts, but it must not change the shared validator or silently reinterpret
the 296 errata. The proposed canonical format remains blocked until the
product ledger, banlist scope, Expert Rules boundary, and early engine gaps
have evidence-backed implementation decisions.

## Source hierarchy

The companion JSON packet records URLs, evidence labels, short notes, and
the exact audit counts consumed by the tests. Primary Konami product/event
pages outrank community databases. The original-rulebook transcription is
used for historical text but is clearly labelled as a later transcription of
the scan. Format Library, YGOPRODeck, and historical-format sites are
cross-checks only. Unresolved conflicts remain unresolved.

## Starter Rules / Expert Rules timeline

The available evidence supports the following bounded timeline; it does not
prove one clean Tokyo Dome transition date:

| Date or interval | Ruleset/evidence | Evidence class | Status |
| --- | --- | --- | --- |
| 1999-02-04 | Original Starter Box Official Rules baseline | later transcription of period rulebook | publication baseline resolved |
| 1999-05-05 | Expert Rules introduced in parallel with Official Rules | strong secondary reconstruction | date supported secondarily; primary publication source unlocated |
| 1999-08-26 | Tokyo Dome national OCG event | period event/product evidence | event rulesheet absent; Expert versus event-specific hybrid unresolved |
| 2000-04-01 to 2000-04-20 | New Expert transition around Magic Ruler | strong secondary reconstruction with boundary conflict | bounded, not exact |

The Expert reconstruction reports Level 5/6 requiring one Tribute, Level 7+
requiring two, removal of the original one-Spell/one-Trap activation limits,
and Fusion materials from the hand. The first rulebook transcription instead
describes one Normal Summon/Set, one Spell activation, one Trap activation,
and Fusion materials on the field. The best working hypothesis is Expert
Rules by August because the secondary history says recognized tournaments used
them; that is an inference, not Tokyo Dome-specific primary proof. The gate
therefore records “likely Expert Rules, not proven for this event” and keeps
canonicalization blocked.

## Main / Battle / Main correction and engine experiment

The first rulebook transcription says Battle Phase occurs during Main Phase
and, after Battle, that play remains in Main unless the player moves to End
Phase. Absence of the label “Main Phase 2” is therefore not evidence that
post-battle Summons, Sets, or activations were illegal.

A real pinned-core experiment sets up a face-up Summoned Skull, a Normal
Summonable Giant Rat in hand, attacks, and declines further battle:

| Config | Flags | Observed |
| --- | --- | --- |
| A | `DUEL_MODE_MR1 \| DUEL_ATTACK_FIRST_TURN` | Draw → Standby → Main → Battle → Main2 → End; post-battle idle prompt offers and executes Normal Summon |
| B | A plus `DUEL_NO_MAIN_PHASE_2` | Draw → Standby → Main → Battle → End; no post-battle idle prompt and no summon |
| C | MR1 with `DUEL_OCG_OBSOLETE_IGNITION` removed, plus attack-test flag | Same phase/action result as A |

`DUEL_NO_MAIN_PHASE_2` is rejected. The modern Main2 label is anachronistic,
but its legal action window is closer to the historical Main → Battle → Main
sequence. `DUEL_OCG_OBSOLETE_IGNITION` is not justified merely by the age or
OCG territory of the event. The reproducible test is
`tests/engine/test_tokyo_dome_rules.py` and is skipped when the pinned Linux
core/checkouts are unavailable.

## Explicit engine gaps

The period deck-out wording says that when a player cannot draw, the player
with higher LP wins, with simultaneous LP zero a draw. Later historical
reconstructions place the change to modern “deck-out player loses” semantics
at the New Expert/Magic Ruler transition, but that secondary boundary does
not prove the Tokyo Dome rule. Pinned ocgcore has no flag for the higher-LP
comparison. The sanctioned repository `init.lua` hook can patch scripted
effects, but cannot reliably intercept the core's draw-exhaustion win decision;
exact reproduction would need core/runtime support. This is competitively
meaningful and blocking, not a documentary-only gap.

The original battle table directly compares ATK and DEF: higher ATK destroys
the lower ATK monster and inflicts the difference; equal ATK destroys both
with no damage; attacking lower ATK into DEF destroys neither and damages the
attacker by the difference; higher ATK into DEF destroys the defender with no
damage; direct attacks apply when no opposing monster exists. It does not
describe the modern Damage Step/timing model. `DUEL_0_ATK_DESTROYED` can
approximate the literal equal-zero result, but
`DUEL_6_STEP_BATLLE_STEP` only changes selected chain windows and does not
remove the modern Damage Step. Exact timing would require wider core/script
changes and remains a blocker.

## Deck construction and pool caveats

The historical limits are Main minimum 40 with no upper bound, Side exactly
10, and a separate Fusion Deck with no upper bound located in the available
source. The schema stores integer pairs, so the honest research distinction
is historical `[40, null]` / `[10, 10]` / `[0, null]` versus host-enforceable
`[40, 999]` / `[10, 10]` / `[0, 999]`. The `999` values are finite EDOPro
client ceilings, not historical maxima. A nullable or explicit `unbounded`
schema value is desirable, but no schema change is required under the current
project design's host-enforceable approximation model.

The current repository has 411 release products and zero `ocg*` release
events. A community 370-identity cross-check has 249 identities in the index
and 121 absent; it is not a substitute for the deferred OCG release ledger.
Konami dates Booster 4, Premium Pack, and Tokyo Dome event products to August
26, but the source does not establish whether distributed cards were legal in
that same event. The August 25 cutoff is therefore retained as a reproducible
community reconstruction, not claimed as an official tournament pool.

## Banlist status

The commonly reconstructed July 1999 list limits Dark Hole, Raigeki, and Trap
Hole, with no Forbidden or Semi-Limited entries. Available historical sources
remain secondary and disagree about broad July effectiveness versus an
event-specific Tokyo Dome application. No primary dated list or event
rulesheet has been certified. The banlist remains a blocker, and this gate
does not create `data/banlists/ocg-1999-07.json`.

## Required architecture verdict

### B. EXISTING ARCHITECTURE SUFFICIENT WITH DOCUMENTED HOST/ENGINE APPROXIMATIONS

This verdict means storage and validation can represent a future
host-enforceable research artifact: `OCG` format region, `ocg-jp` release
territory, cutoff pool, finite host deck limits, candidate flags, and explicit
known gaps. It does not mean historical exactness or canonical readiness.

The independent blockers are the unproven Starter/Expert event boundary,
early deck-out, early battle timing, formal chain/priority boundary, release
ledger, missing identities, disputed banlist, and unresolved errata coverage.
No shared schema or runtime mutation was justified by this gate.

## Canonicalization blocker ledger

| Blocker | Status | Evidence-backed reason |
| --- | --- | --- |
| Format name/date convention | RESOLVED WITH APPROXIMATION | Tokyo Dome / August 25 is a reproducible community convention, not an official format record. |
| Event/card-pool cutoff | UNRESOLVED | Same-day products/distribution are documented; same-event legal use is not. |
| OCG release ledger | BLOCKING | No current `ocg*` product events. |
| Missing card identities | BLOCKING | 121 community cross-check identities are absent from the current index. |
| Banlist | BLOCKING | Three-card July reconstruction and broad-vs-event scope remain secondary/disputed. |
| Starter Rules vs Expert Rules effective boundary | BLOCKING | Expert is likely, but Tokyo Dome adoption is not proven. |
| Main/Battle/Main phase behavior | RESOLVED WITH APPROXIMATION | Main2 action window is closer; `DUEL_NO_MAIN_PHASE_2` is rejected. |
| First-turn draw | RESOLVED | Period rulebook and default absence of `DUEL_1ST_TURN_DRAW` agree. |
| First-turn attack | RESOLVED | Period rulebook and default absence of `DUEL_ATTACK_FIRST_TURN` agree. |
| Hand limit | RESOLVED WITH APPROXIMATION | No limit is documented; `DUEL_NO_HAND_LIMIT` matches the axis. |
| Deck-size representation | RESOLVED WITH APPROXIMATION | `[40,999]` is a host ceiling, not historical infinity. |
| Side/Fusion deck constraints | RESOLVED WITH APPROXIMATION | Side exact 10 fits; Fusion maximum is unlocated and host-bounded. |
| Deck-out rule | BLOCKING | Higher-LP win is meaningful and has no pinned-core mechanism. |
| Battle-calculation semantics | BLOCKING | Direct historical result table is not the modern Damage Step model. |
| Chain/Spell-Speed semantics | BLOCKING | Formal boundary is absent from available early evidence and flags. |
| Errata chronology | RESOLVED | All 296 selections and exact identity sets are mechanically frozen. |
| Errata implementation coverage | BLOCKING | 150 ambiguous; 47 unresolved candidate occurrences/records. |
| Engine representability | BLOCKING | Exact early deck-out, battle timing, and rule boundary are not all executable. |
| Schema representability | RESOLVED WITH APPROXIMATION | Host limits are storable; unbounded support remains desirable. |

This hardening gate creates no canonical Tokyo Dome format, banlist, pool,
rule profile, generated output, release ledger, or errata mutation. Existing
GOAT, Edison, and Tengu artifacts remain the only canonical formats.
