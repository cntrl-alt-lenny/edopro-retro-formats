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

## Release ledger certification (2026-08)

A follow-on task built the actual Japanese OCG release ledger this gate had
deferred, through 1999-08-25 inclusive. It is release-ledger/card-identity
certification only - it does **not** create the Tokyo Dome format, banlist,
pool, or rule profile, and it does **not** resolve any of the other blockers
below (banlist scope, Starter/Expert boundary, deck-out, battle timing,
chain/priority, errata implementation coverage, engine representability).
Full structured results live in
`docs/research/yugi-kaiba-format-source-packet.json` under
`release_ledger_certification`, mechanically pinned by
`tests/test_ocg1999_release_certification.py`.

**Verdict: RESOLVED WITH NONBLOCKING GAPS.**

- **Coverage window:** `ocg-jp`, 1999-02-01 through 1999-08-25, status
  `complete` (`data/releases/coverage.json`).
- **20 certified products**, hand-curated (`curated: true`) from Yugipedia's
  OCG Series 1 set/product/card pages and cross-checked for completeness
  against Yugipedia's own "Series 1 sets" navigation template: Vol.1-4,
  Booster 1-3, Starter Box, Starter Box: Theatrical Release, the Starter Box
  pre-order promo, the three Limited Edition Yugi/Kaiba/Joey packs, the
  Official Guide Starter Book promo, the Duel Monsters II: Dark Duel Stories
  video-game promo cards and both Game Guide promos, The Valuable Book 1
  promos, and the Duel Monsters National Tournament attendance and (partial)
  prize-card products. The earliest certified distribution is the National
  Tournament attendance card, 1999-02-21 - 12 days before Vol.1.
- **5 research anomalies**, all `resolved-safe` and none pool-impacting, in
  `data/releases/gaps.json` (`gap-ocg1999-*`): the National Tournament's
  top-placer trophy tier (Black Luster Soldier/Zera the Mant/Super
  War-Lion/Fiend's Mirror - one-of-a-kind metal cards, 1-4 physical copies
  ever made; Black Luster Soldier's is additionally a genuinely distinct
  historical identity from the modern Ritual Monster), the Tokyo Dome
  invitation Ticket cards (`This card cannot be used in a Duel.`), and three
  small redundant promo distributions (V Jump August 1999 Special Present,
  V Jump Festa 1999 - which also carries an unresolved Yugipedia/Konami date
  conflict, harmless either way - and the DM2 trial-meeting card).
- **Card identity resolution:** all 121 identities the prior gate's community
  cross-check found absent are now accounted for - 119 added to
  `data/cards/index.json` mechanically via the standard BabelCDB-backed
  importer (real product printings, pinned revision
  `0659607453a7d79d1adefbfe1ef7477d3c92434c`, unchanged; zero invented
  passcodes), and 2 (Final Flame, Ultimate Offering) resolved as +/-10
  artwork-variant aliases of already-canonical cards rather than new
  identities. 0 remain unresolved.
- **Candidate pool:** a pure `evaluate_cutoff` derivation (region `OCG`,
  territory `ocg-jp`, cutoff `1999-08-25`, zero manual
  `cutoff.include`/`exclude`/`exclude_products` entries) yields exactly
  **370 canonical cards**, 0 ambiguous, 0 unknown printings. Digest (sha256
  of the sorted `[{passcode,name}]` list):
  `f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`. This
  pool is derived in tests/research only - `data/pools/1999-08-tokyo-dome.json`
  is deliberately not written.
- **Community cross-check:** compared against the independent YGOPRODeck
  "1999 Tokyo Dome Card Pool" cube (370 cards; snapshot in
  `docs/research/ocg1999-tokyo-dome-community-candidates.json`, diff in
  `docs/research/ocg1999-tokyo-dome-community-diff.json`): **common 370,
  ledger-only 0, community-only 0** after canonicalization. The only raw
  differences (4, before canonicalization) are all the same category -
  alias/artwork canonicalization - and collapse cleanly.
- **August 26 boundary audit:** Booster 4 (40 cards, 5 of them reprints
  already certified via Vol.4 and included in the pool through that earlier
  origin only), Premium Pack (10 cards, including the "Exodia the Forbidden
  One" head-piece reprint), and the Tokyo Dome attendance (2), participation
  (3, given per-round during the same-day tournament), and prize (3) cards
  are all dated 1999-08-26 and all confirmed absent from the 1999-08-25
  candidate. Counting distinct identities (35 new Booster 4 cards + 10
  Premium Pack + 8 tournament-exclusive = 53; the other 5 Booster 4 card
  slots are the Vol.4 reprints already counted via their earlier source),
  none of the 53 Aug-26-exclusive cards appears in the community cube
  either (corrected 2026-08 recertification: an earlier draft of this
  section said "60", a loose prose figure never backed by any committed
  data or test - the precise count is 53). The Tokyo Dome tournament itself ran August 1-26 (regional
  qualifiers into the August 26 Tokyo Dome final), mirroring the February
  1-21 National Tournament already in this ledger; no card or product is
  dated between August 1 and August 25, so this does not affect the cutoff.
  Tournament legality at the event remains unproven either way (unchanged
  from the rest of this gate).
- **Pool-intersected errata audit** (research only, no policy chosen): of
  the 296 frozen global errata records, 6 correspond to a card in the
  370-card pool (`erratum-castle-walls`, `erratum-cocoon-of-evolution`,
  `erratum-crush-card-virus`, `erratum-elegant-egotist`,
  `erratum-reinforcements`, `erratum-ultimate-offering`): 2 determinate (both
  historical, `reuse-upstream`), 4 ambiguous (3 modern-possible, 1
  modern-impossible; 8 candidate occurrences: 4 `reuse-upstream`, 3
  `modern`, 1 `unresolved`).
- **Architecture verdict for this task: A** (existing architecture fully
  sufficient - product-release schema, coverage/gap ledger, card-index
  importer, and `evaluate_cutoff` truthfully represented every historical
  fact this task needed, including the National Tournament trophies' and
  invitation tickets' exclusions and Black Luster Soldier's distinct
  historical identity, with no schema or runtime change). This does not
  revise the format's overall verdict B below, which is about the remaining,
  unrelated engine/host approximation blockers.
- **GOAT/Edison/Tengu preserved exactly**: hash `0x28E9FC02` / pool 3,673 /
  pool 4,562 / hash `0x0CE5BABE` respectively; `dist/` rebuilds byte-identical.

Do **not** read this as "Tokyo Dome is ready for canonical implementation."
The release-ledger/card-identity blocker is resolved; the banlist, Starter
vs. Expert Rules boundary, deck-out, battle-calculation, chain/priority, and
errata-implementation-coverage blockers below are unchanged and remain
BLOCKING.

## Release ledger RECERTIFICATION (2026-08, correction pass)

Independent review of the certification above found primary-source
contradictions in the newly-built 1999 OCG chronology. This repository does
not treat green tests as proof of historical correctness: a follow-on task
re-audited the entire pre-cutoff ledger with five independent research
roles (a Konami-chronology auditor, an early-promo/tournament historian, a
card-identity/alias auditor, an adversarial-test auditor, and a
community-pool comparator), each working from primary sources without
reading the others' conclusions, followed by a separate adjudication pass.
Full detail: `release_ledger_certification.recertification_2026_08` in
`docs/research/yugi-kaiba-format-source-packet.json`.

**Two date corrections** (both discovered independently by three of the
five research channels, plus the author's own direct re-check of Konami's
live database - four convergent confirmations against one contrary, uncited
Yugipedia infobox value):

| Product | Card | Was | Corrected to | Why |
| --- | --- | --- | --- | --- |
| DM2 Game Guide 1 promo | Right Arm of the Forbidden One | 1999-07-08 | **1999-07-13** | The old date copied the unrelated, separately-certified video-game-bundled product's date instead of this strategy-guide book's own. |
| DM2 Game Guide 2 promo | Left Arm of the Forbidden One | 1999-08-05 | **1999-08-10** | Same defect. |

Both corrections were confirmed directly against Konami's own per-card
print-history pages (`card_search.action?ope=2&cid=...`) - each card has
exactly one 1999 printing entry, and it is the corrected date, not the old
one - independently corroborated by Konami's separate product-catalogue
listing page (which files both guide books under a `【書籍】` category,
distinct from the game-bundled promo they were previously conflated with)
and by Japanese publisher (openBD/National Diet Library) ISBN metadata for
both books. Neither correction changes pool membership: both new dates
remain before the 1999-08-25 cutoff.

**One product deleted** as fabricated:
`yu-gi-oh-duel-monsters-national-tournament-prize-cards.json`, which had
claimed a physical `ocg-jp` release on 1999-02-21 of three cards
(Millennium Shield, Megasonic Eye, Yamadron). The root cause was identified
and quoted: Yugipedia's "...National Tournament prize cards" page lists
results by placement tier in a two-column table ("Physical card" / "Video
game card"); the Qualifying tier's Physical-card cell is **blank**, and its
Video-game-card cell (which does list all four names, including Kanan the
Swordmistress) links to `(DM1)`-suffixed pages describing a hidden/
unlockable reward inside the Game Boy title *Yu-Gi-Oh! Duel Monsters*
(1998-12-16, itself already excluded from this ledger as Non-OCG), using a
distinct template with no passcode field at all. Kanan alone is *also*
physically real, but via the wholly separate, correctly-sourced
`yu-gi-oh-duel-monsters-national-tournament-attendance-card` product, kept
unchanged. Konami's official product catalogue has no row for any "prize
cards" product on this date, and each of the three cards' own individual
Konami print-history shows no printing earlier than 1999-06-01 (Limited
Edition: Yugi Pack / Joey Pack, already certified elsewhere in this
ledger). Deleting the fabricated product changes **zero** pool membership:
all three cards remain correctly available via their genuine June 1999
release.

**Net effect:** 20 certified products -> **19**; candidate pool cardinality
and digest **unchanged** (370 cards,
`f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`) - proven,
not assumed, by mechanical re-derivation after the corrections. This is
expected, not suspicious: none of the three defects removed a card's
pre-cutoff availability, only the accuracy of which product/date backed it.
The pool digest is a checksum of `{passcode, name}` pairs only and is
structurally blind to date errors of this kind - it could not have caught
any of the three defects, and did not. What actually catches them now is a
new evidence fixture, `tests/fixtures/ocg1999-official-chronology.json`,
assembled directly from Konami's own official product database and never
generated from this repository's own product files (see that file's own
header for exactly how), which `tests/test_ocg1999_release_certification.py`
compares the live release data against, plus dedicated adversarial tests
proving each of the three defects (and several synthetic variants) would
now be caught.

Also corrected: honest source provenance. Every one of the 19 remaining
products' `release_events[].sources` previously cited `konami-card-database-ja`
in a way that implied direct verification while `data/sources.json` itself
disclosed reliance on Yugipedia's aggregation instead. All 19 have now been
directly re-verified against Konami (either its per-card print-history
pages or its product-catalogue listing, both newly registered as their own
distinct sources) and their `status` upgraded from `reported` to `verified`
where two or more independent official channels now genuinely agree.

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

**Update (2026-08, release-ledger certification):** the release-ledger and
card-identity blocker described in this section is now RESOLVED. See
"Release ledger certification (2026-08)" below for the full result; this
section is kept as the original historical record of what was blocking.

Originally: the official product chronology supported an OCG-Japan
release-cutoff pool, but the repository had 411 release products and zero
`ocg*` release events. A community singleton cross-check contained 370 card
identities; 249 were in the card index and 121 were absent. That cross-check
was not a substitute for a product-by-product OCG ledger - building one was
exactly this gate's next task, now complete.

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

**Update (2026-08, recertified):** the repository now has 430 release
products, 19 of them a certified `ocg-jp` ledger through 1999-08-25 (see
"Release ledger certification" and "Release ledger RECERTIFICATION"
above); the 370-identity community cross-check is fully resolved (370/370
in the index, 0 absent). Originally: the repository had 411 release
products and zero `ocg*` release events, and the community cross-check had
249 in-index / 121 absent. An intermediate 2026-08 pass certified 20
products; an independent audit then found and corrected 3 defects (2 wrong
dates, 1 fabricated product), landing on the current 19.

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
| OCG release ledger | RESOLVED | 2026-08: a real, sourced, product-by-product `ocg-jp` ledger exists through 1999-08-25 (19 products after the 2026-08 recertification's correction - see "Release ledger certification" and "Recertification" sections above; 0 unresolved pool-impacting gaps). |
| Missing card identities | RESOLVED | 2026-08: all 121 community cross-check identities accounted for (119 added to the card index, 2 collapsed as artwork-variant aliases). |
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

## Rules and restriction-list research gate (2026-08)

A second, independent 5-agent research swarm (A: restriction-list chronology,
B: Tokyo Dome event documents, C: early OCG rules chronology, D: ocgcore
representability, E: adversarial auditor) plus a direct F adjudication pass
was run against this same commit lineage to answer two questions the prior
hardening gate above left open: what restriction list applied to Japanese OCG
play at the Tokyo Dome boundary, and what game rules were actually in force
there versus what current engine architecture can represent. Full structured
findings are in `docs/research/yugi-kaiba-format-source-packet.json` under
`tokyo_dome_rules_and_restriction_research_2026_08`. This is a second,
additive research pass - it does not delete or silently rewrite anything
above; where it disagrees with a verdict recorded above, the disagreement is
called out explicitly rather than papered over (see "Reconciliation" below).

**Verdict: BLOCKED_BY_BOTH** (historical evidence AND engine representation).
Still no canonical Tokyo Dome format, banlist, pool, rule profile, or lflist
was created by this pass. `dist/`, runtime behavior, schemas, and the errata
model were not touched.

### Format identity - unchanged, with a new caveat

The recommended identity is unchanged from the section above: id
`1999-08-tokyo-dome`, display name "Tokyo Dome Format", region OCG, snapshot
**1999-08-25** (pre-event, not event-day). The swarm found no evidence
justifying a move to an event-day snapshot - if anything it found evidence
cutting against one: the event's own headline attendance promo, Gate
Guardian, is absent from the certified 370-card pre-event pool, and so are
all three of its Fusion Material monsters (Suijin, Kazejin, Sanga of the
Thunder) - directly reconfirmed this session by recomputing the release
cutoff against live repo state. Anyone restricted to the certified pre-event
pool could not have Fusion Summoned Gate Guardian, regardless of exactly when
its materials were later released. (Community card-list aggregators converge
on Vol.5, 1999-09-23 - a month after Tokyo Dome - as their actual first
OCG-JP release; a direct Konami-database fetch to confirm that date primarily
could not complete in this sandbox, so that specific date is held at medium,
not high, confidence.) Separately, and newly: whether the Tokyo Dome tournament
even concluded as a coherent single-day event on August 26, 1999 is now in
genuine doubt. Multiple independent Japanese retrospective sources describe
crowd-control failure severe enough to require riot police, with one strand
of testimony suggesting the finals may not have concluded at the venue and
were possibly re-held regionally. No period (1999) document confirming or
denying this was found by either the event-document specialist or the
adversarial auditor despite deliberate searching in English and Japanese.
This is reported as an open historical question, not resolved.

### Restriction list - content corroborated, scope BLOCKED

The 3-card content (Raigeki, Dark Hole, Trap Hole, each Limited to 1 copy,
single-tier - no "Forbidden" tier existed in Japan until March 2004) remains
well corroborated across independent sources and is not in dispute. What
broke this pass: the adversarial auditor found that the two sources this
packet already cites for that list - Yugipedia and ocg-card.com - actually
describe **different objects** when read closely. Yugipedia frames the list
as Konami's first official, nationwide restriction; ocg-card.com frames what
looks like the same 3 cards as rules for one specific 1999 qualifying event,
not a blanket restriction on all OCG play. Neither is a Konami-original
document, and neither source states which reading is correct. Applying the
evidence hierarchy gives no way to prefer one tier-5/6 source's framing over
the other's when they disagree about scope, not just detail - so per the
task's own instruction, this is left **BLOCKED** rather than guessed.
Separately, the "July 1999" date already carried in this packet's
`banlist.working_id` was traced to a specific 2017 Yugipedia edit whose own
cited source does not, on direct re-read, state a July date anywhere - that
date should be treated as an unverified placeholder, not a finding.

On the software side: a single-tier, Limited-only restriction list needs **no
schema or model change** - `BanlistEntry`'s status enum and the
`UNLIMITED_COUNT=3` default already support it. The blocker here is
historical, not architectural.

### Rule chronology - several new PROVEN facts, two newly-flagged disputes

Walking the rulebook lineage from the 1999 Starter Box rulebook forward
turned up several facts this packet had not previously stated explicitly as
PROVEN with a period-scan citation: single Main Phase / no Main Phase 2
concept, no first-turn draw, tribute-summon requirements for level 5+/7+,
Fusion Deck via Polymerization, a 6-card hand limit with end-of-turn discard,
deck-out as a loss condition, and the original Set (face-down defense)
procedure. Two areas are explicitly **UNKNOWN**, not resolved either way:

- **First-turn attack legality.** This directly contradicts the "RESOLVED"
  verdict this packet's own blocker ledger above already recorded for this
  row. The adversarial auditor located secondary sources suggesting
  first-turn attacks may have been *allowed* at the original rulebook stage,
  with a prohibition arriving only in a later 1999 revision - the opposite of
  what the earlier hardening pass assumed. Neither reading is backed by a
  primary source specific to the original printing. **This packet's prior
  "RESOLVED" verdict for first-turn attack should now be read as weaker than
  its label states**, pending a primary source either way. See the packet
  JSON's `reconciliation_with_prior_gate` block for the full detail - this
  contradiction is deliberately not smoothed over.
- **Spell/Trap chain resolution and priority.** No source, primary or
  secondary, conclusively describes the original rulebook's procedure for
  resolving multiple responses. `docs/research/ocgcore-flags.md` already
  documents there is no flag governing this at all - if evidence later
  confirms a non-modern 1999 model, this becomes a genuine engine gap, not
  just a historical unknown.

The already-recorded "Deck-out rule: BLOCKING" row in the ledger above (the
possible higher-LP-wins alternative to strict deck-out loss) is **not**
resolved by this pass either - this session only confirmed the simpler fact
that deck-out was *a* loss condition, and did not investigate the higher-LP
nuance. That blocker stands as previously recorded.

Both the rules specialist and the adversarial auditor flagged and excluded a
category of bad source: retrospective "how 1999 OCG rules worked" articles
that collapse multiple distinct 1999 rule revisions into one undifferentiated
bucket. None of the PROVEN facts above rely on that kind of source.

### Engine representability - decomposed, not preset-based

Per the task's instruction, composite presets were rejected in favor of
per-flag classification. Exactly representable with no flag needed: first-turn
draw skip, tribute/advance summon, Fusion Deck/Summon, hand limit, deck-out.
Representable by omission-default: the original Set procedure. Approximated:
single Main Phase, where `DUEL_NO_MAIN_PHASE_2` matches the headline "no
Main Phase 2" behavior but also removes a legal post-battle action window the
actual 1999 single-Main-Phase model preserved - already established by the
existing `tests/engine/test_tokyo_dome_rules.py` experiment and confirmed,
not re-derived, this pass (`H.available()` remains `False` in this sandbox,
so no new pinned-core test was run). Unknown-because-historically-unresolved:
first-turn attack, chain/priority. Not representable without runtime changes:
deck size, side deck, match/tiebreaker rules, starting LP as a tournament
rule - these live at a client/host-config layer this repo has not built,
confirmed and not newly discovered.

`DUEL_MODE_MR1` and `DUEL_MODE_GOAT` were both explicitly evaluated and
rejected as starting points for any future rule profile: MR1 bundles at
least one sub-flag (the obsolete-ignition family) whose period correctness
for August 1999 specifically was not independently re-verified this pass, and
GOAT is tuned for a 2005 TCG boundary. Any future profile must set and cite
flags individually.

### Event-day card pool - unchanged, 370 cards

No source establishes that any card first distributed on August 26, 1999
(attendance promos, prize cards, Premium Pack, Booster 4) was legal in decks
actually played that day, as opposed to being a take-home souvenir. The Gate
Guardian case above is affirmative evidence against the
"released-at-the-event-implies-legal-at-the-event" assumption. The certified
pre-event pool - 370 cards, digest
`f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb` - was
independently recomputed this session from live repo state and is unchanged.
No August 26 card is added.

### Errata intersection - accounting only, 296/296 unchanged

Recomputed live (not from memory of the prior session): 6 of the 296 v2
errata records intersect the 370-card pool at the 1999-08-25 snapshot -
`erratum-crush-card-virus` and `erratum-reinforcements` are determinate;
`erratum-castle-walls`, `erratum-cocoon-of-evolution`,
`erratum-elegant-egotist`, and `erratum-ultimate-offering` remain ambiguous.
No record was modified and no new chronology was invented to make the
ambiguous four resolve.

### Final verdict

**BLOCKED_BY_BOTH.** Historically: restriction-list scope, first-turn-attack
legality, chain-resolution model, and Tokyo-Dome-specific tournament
structure are all unresolved at the confidence this gate requires.
Architecturally: even the historically-proven facts include at least one
(single Main Phase) that is only approximated, and the client/host-config
layer for tournament-structure rules does not exist. Neither blocker alone
would be sufficient to stop here on its own strength - together they are.
This does not mean the format is unbuildable in principle; it means
canonicalization is not authorized yet.
