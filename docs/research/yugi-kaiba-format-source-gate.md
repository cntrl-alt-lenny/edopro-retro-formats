# Early OCG format source and implementation gate

Status: research gate only. This document does not create an early OCG
format, banlist, card pool, or rule profile.

## Current authoritative state (read this first)

> This section is the single mechanically-checkable current-state summary
> for the whole document, and is pinned by
> `test_gate_md_current_state_header_matches_authority` in
> `tests/test_yugi_kaiba_format_gate.py`. Every section below this one is
> preserved as point-in-time research history for audit purposes - where a
> later section corrected an earlier one, the correction is current, the
> earlier prose is not. **If any section below appears to disagree with
> this one, this section and the structured JSON at
> `tokyo_dome_research_current` in `yugi-kaiba-format-source-packet.json`
> govern, not the older prose.**

- **OCG release ledger:** 19 certified products (not 20 - an intermediate
  2026-08 pass certified 20, then an independent recertification found and
  corrected 3 defects), 370-card candidate pool, digest
  `f65d30b07d231c1a1913b36b659dfc8e6d536fb2c7db0ffa36cd65f6e57ba1eb`.
- **Expert Rules primary source:** LOCATED and personally inspected
  (archive.org scan of the 1999-05-05 Shueisha/Studio Hard *Official Guide
  Starter Book*, pages 101-109, 2026-08-29). Expert Rules are directly
  documented in that guide - `PROVEN`, not a secondary reconstruction. What
  remains unproven: the guide does not state a normative effective date
  (`SUPPORTED_BUT_INCOMPLETE`), and no Tokyo Dome event-specific rulesheet
  has been located, so Tokyo-Dome-specific Expert Rules adoption is
  `UNKNOWN`.
- **Restriction list:** best current hypothesis is a tournament-specific
  (not nationwide) Limited-to-1 list for Raigeki, Dark Hole, and Trap Hole,
  research confidence `MODERATE-TO-GOOD` (personally inspected 2004
  Shueisha *Master Guide* p.84). Canonicalization status is
  `UNRESOLVED_BLOCKING` regardless - no contemporaneous 1999 document has
  been located.
- **Full Chain/Spell-Speed/priority system:** historical adoption by
  Tokyo Dome is `UNKNOWN`. It is **not** an independent unconditional
  engine blocker. The narrower, `PROVEN`/bounded paradigm that *is* a
  confirmed unconditional engine blocker is the Battle-Phase Traps-only
  restriction (`trap_activation_frequency`) - see
  `tokyo_dome_research_current.architecture_verdict_detail.`
  `engine_representation_blockers`.
- **Unconditional engine blockers (independent of any unresolved history):**
  deck-out LP-comparison, the Battle-Phase Traps-only response restriction
  (`trap_activation_frequency`), and the early battle-calculation attacker-
  recoil quirk. **Re-adjudicated 2026-08-29 (session 2):** these three no
  longer rest on "PROVEN at Starter Box + no located evidence of change"
  (the same silence-based reasoning already correctly rejected for full
  chain/priority above) - a second, independently-dated primary source
  (the same 1999-05-05 guide, a *different* chapter than the Expert Rules
  one) affirmatively re-documents all three as unchanged ~113 days before
  Tokyo Dome, and externally-corroborated evidence places the eventual
  change ~8 months *after* Tokyo Dome. See "Continuity-evidence closure
  pass" near the end of this document and
  `tokyo_dome_research_current.positive_continuity_evidence` for the full
  chain.
- **Architecture verdict:** `BLOCKED_BY_BOTH` (unresolved historical
  evidence and unrepresentable engine behavior each independently block
  canonicalization).
- **No canonical Tokyo Dome format, banlist, pool, or rule profile exists.**
  GOAT, Edison, and Tengu are unaffected.

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
| Banlist | best current hypothesis: tournament-specific, three cards Limited to 1 (Raigeki, Dark Hole, Trap Hole) - canonicalization still `UNRESOLVED_BLOCKING`; see "Current authoritative state" above, not the July-1999 framing this row originally used |
| Next conventional format | `Exodia`, community convention, April 10, 2000 |

This is a research recommendation, not approval to add canonical files.
*(Original 2026-XX framing, superseded by "Current authoritative state"
above: the target was called "representable with format-local
approximations" without qualifying that against the current unqualified
architecture verdict.)* The current, unqualified architecture verdict is
`BLOCKED_BY_BOTH` (historical evidence AND engine representability each
independently block canonicalization) - see "Current authoritative state"
above. Schema/host data-shape representability specifically (a narrower,
different question) remains sufficient with documented approximations; it
does not by itself make the format ready for canonicalization.

## Release ledger certification (2026-08)

> **Superseded by the recertification below.** This pass's headline count
> of **20 certified products** was later found to include 1 fabricated
> product and 2 wrong dates; "Release ledger RECERTIFICATION" immediately
> below corrects it to the current, authoritative **19**. Read this section
> for the certification methodology, not for the product count.

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
  revise the format's overall canonicalization verdict, which is about the
  remaining, unrelated engine/host approximation blockers - see "Current
  authoritative state" at the top of this document (`BLOCKED_BY_BOTH`), not
  a "verdict B" (that label no longer exists anywhere in this document).
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

> **Update (2026-08-29):** the paragraph below originally said the Expert
> Rules "primary publication source has not been located." That is no
> longer true - the guide was located and personally inspected; see
> "Primary-source resolution pass: 2026-08-29" near the end of this
> document and "Current authoritative state" at the top. The rest of this
> section's Starter Box transcription content is unaffected and remains
> current.

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
Spell/Trap activations, and allowed Fusion materials from the hand. The
primary publication source for Expert Rules - the 1999-05-05 Official Guide
Starter Book - was later located and personally inspected (2026-08-29): it
directly documents Expert Rules as a real Konami ruleset (`PROVEN`), but its
own wording does not say they became the normative effective ruleset that
day (`SUPPORTED_BUT_INCOMPLETE`), and no Tokyo Dome event-specific rulesheet
has been located, so Tokyo-Dome-specific adoption remains `UNKNOWN`
(not "likely" - do not silently merge the two rulesets, and do not read
"documented in a guide" as "adopted at this event").

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

> **Superseded (2026-08-29):** the "July 1999, possibly nationwide" framing
> below is the ORIGINAL working hypothesis this gate started from. It has
> since been researched further and materially revised - the current best
> hypothesis is tournament-specific (not nationwide), with meaningfully
> better-than-original research confidence (`MODERATE-TO-GOOD`, from a
> personally-inspected 2004 retrospective), while canonicalization remains
> `UNRESOLVED_BLOCKING` regardless. See
> `tokyo_dome_research_current.restriction_list_current` in the packet and
> "Current authoritative state" at the top of this document - do not use
> the paragraph below as the current scope framing.

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

## Architecture decision (schema/host representability only)

> **Scope note (2026-08 consistency pass):** this section answers a narrow
> question - can existing schemas and host configuration encode the SHAPE of
> a Tokyo Dome format record? It does NOT answer whether the Tokyo Dome
> format is ready for canonicalization. That separate, current question is
> answered only in "Final hardened research state" near the end of this
> document (verdict: `BLOCKED_BY_BOTH`), and only by
> `tokyo_dome_research_current.architecture_verdict` in the packet JSON. In
> the packet, this section's structured counterpart now lives at
> `schema_host_architecture_assessment`, not `architecture`.

### Schema/host representability: sufficient with documented approximations

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

> **Update (2026-08-29):** the table and paragraph below predate the
> primary-source resolution pass. The 1999-05-05 row's "primary publication
> source unlocated" status is no longer true - see "Current authoritative
> state" at the top of this document and "Primary-source resolution pass:
> 2026-08-29" near the end for the corrected evidence and status.

The available evidence supports the following bounded timeline; it does not
prove one clean Tokyo Dome transition date:

| Date or interval | Ruleset/evidence | Evidence class | Status |
| --- | --- | --- | --- |
| 1999-02-04 | Original Starter Box Official Rules baseline | later transcription of period rulebook | publication baseline resolved |
| 1999-05-05 | Expert Rules introduced in parallel with Official Rules | `PROVEN` (guide located and personally inspected, 2026-08-29) that Expert Rules are documented; normative effective date is `SUPPORTED_BUT_INCOMPLETE` | primary source located and personally inspected; see "Primary-source resolution pass: 2026-08-29" |
| 1999-08-26 | Tokyo Dome national OCG event | period event/product evidence | event rulesheet absent; Tokyo-Dome-specific adoption `UNKNOWN` |
| 2000-04-01 to 2000-04-20 | New Expert transition around Magic Ruler | strong secondary reconstruction with boundary conflict | bounded, not exact |

The Expert reconstruction reports Level 5/6 requiring one Tribute, Level 7+
requiring two, removal of the original one-Spell/one-Trap activation limits,
and Fusion materials from the hand. The first rulebook transcription instead
describes one Normal Summon/Set, one Spell activation, one Trap activation,
and Fusion materials on the field. Expert Rules content is now `PROVEN`
documented by 1999-05-05; whether Tokyo Dome itself used them remains
`UNKNOWN`, not "likely" - that is a genuine unresolved question, not merely
an unproven inference from secondary history. The gate therefore keeps
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

> **Update (2026-08-29):** research confidence on scope has since improved
> (personally-inspected 2004 Master Guide p.84 points to a tournament-
> specific reading, `MODERATE-TO-GOOD` confidence) - see
> `tokyo_dome_research_current.restriction_list_current` and "Current
> authoritative state" at the top of this document. The bottom-line
> conclusion below (banlist remains a blocker; no
> `data/banlists/ocg-1999-07.json`) is still correct; the "broad July
> effectiveness versus event-specific" framing itself is superseded.

The commonly reconstructed July 1999 list limits Dark Hole, Raigeki, and Trap
Hole, with no Forbidden or Semi-Limited entries. Available historical sources
remain secondary and disagree about broad July effectiveness versus an
event-specific Tokyo Dome application. No primary dated list or event
rulesheet has been certified. The banlist remains a blocker, and this gate
does not create `data/banlists/ocg-1999-07.json`.

## Schema/host architecture verdict (superseded as "the" verdict - see below)

> This is NOT the current unqualified Tokyo Dome architecture/canonicalization
> verdict. It is the same narrow schema/host representability finding as
> above, restated at the point this document originally required a verdict.
> The current, unqualified verdict is `BLOCKED_BY_BOTH` - see "Final hardened
> research state" near the end of this document.

### Schema/host representability: sufficient with documented approximations

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

## Rules and restriction-list research gate (2026-08) - SUPERSEDED, ARCHIVED

> **This entire section is SUPERSEDED and ARCHIVED.** It was independently
> reviewed and rejected as a historical-rules gate: the integrating
> adjudicator of this pass promoted subagent summaries to PROVEN without
> personally re-reading the load-bearing historical source closely enough,
> producing several wrong conclusions (first-turn attack marked ambiguous
> when it is proven prohibited; a guessed "probable 2000 LP" when the
> primary source says 8000; deck-out marked exactly representable when it
> is a genuine engine gap; an internal contradiction about the post-battle
> Main Phase; hand-limit and Tribute Summon wrongly promoted to proven).
> Its corresponding JSON has been moved wholesale to
> `docs/research/yugi-kaiba-format-source-packet.json` under
> `superseded_findings.rejected_2026_08_rules_and_restriction_research` -
> that namespace is unmistakably archival and must never be read as
> current. **Do not use anything in this section as current research.** For
> the current, hardened research state, skip to "Final hardened research
> state (2026-08, third pass)" near the end of this document, or read
> `tokyo_dome_research_current` in the packet JSON. This section is kept
> below, unedited, only as a preserved historical record of what the
> rejected pass said and why it was wrong.

A second, independent 5-agent research swarm (A: restriction-list chronology,
B: Tokyo Dome event documents, C: early OCG rules chronology, D: ocgcore
representability, E: adversarial auditor) plus a direct F adjudication pass
was run against this same commit lineage to answer two questions the prior
hardening gate above left open: what restriction list applied to Japanese OCG
play at the Tokyo Dome boundary, and what game rules were actually in force
there versus what current engine architecture can represent. This pass's
findings were later found untrustworthy in their methodology (see banner
above) - what follows is preserved verbatim as archived history only.

**Verdict at the time (later superseded): BLOCKED_BY_BOTH** (historical
evidence AND engine representation). Still no canonical Tokyo Dome format,
banlist, pool, rule profile, or lflist was created by this pass. `dist/`,
runtime behavior, schemas, and the errata model were not touched.

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

## Corrective rules gate (2026-08, second pass) - CORE FINDINGS SURVIVE, HARDENED FURTHER BELOW

> **This section's JSON has moved and several specific claims were further**
> **recalibrated by a third pass.** Its structured content used to live under
> the packet key `tokyo_dome_rules_corrective_gate_2026_08` - that key no
> longer exists. Its core corrections (the five items below) were correct
> and survive, now under `tokyo_dome_research_current` in the packet, with
> three refinements: (1) the May 5, 1999 Expert Rules date is further
> downgraded from this pass's implied "reasonable confidence" to
> `STRONG_SECONDARY_RECONSTRUCTION`; (2) the restriction list's single
> `MODERATELY RESOLVED, not fully settled` field is split into a separate
> research-confidence field (now upgraded, after personally inspecting the
> actual cited Master Guide page) and a canonicalization-readiness field
> (still explicitly BLOCKING); (3) the architecture verdict is re-derived
> distinguishing historical-evidence blockers from engine-representation
> blockers explicitly. See "Final hardened research state (2026-08, third
> pass)" near the end of this document for the current, authoritative
> narrative, and `tokyo_dome_research_current` in the packet JSON for the
> current, authoritative structured data. This section is otherwise kept
> below, unedited, as a preserved record of this pass's own reasoning.

The rules/restriction-list gate immediately above was independently reviewed
and **rejected** as a historical-rules gate - despite clean engineering and
useful restriction-list research - because the integrating adjudicator
promoted agent summaries to PROVEN without personally re-reading the
load-bearing historical source closely enough. This section is a corrective
pass, not a replacement: it does not delete anything above, but it corrects
five specific wrong or self-contradictory conclusions and replaces the flat
`rule_chronology` with a mechanically explicit three-tier evidence matrix
(original Starter Box state / later-1999 Expert Rules state / Tokyo-Dome-
effective state) that is never allowed to collapse into one bucket. (At the
time this was written, its structured detail lived at the packet key noted
in the banner above; that key has since been renamed - see the banner.)

**Methodology change.** Before dispatching a second 6-agent swarm (A: Starter
Box forensic reader, B: later-1999 chronology, C: Tokyo-Dome-specific, D:
restriction-list re-verification, E: engine representability, F: adversarial
audit), the integrating adjudicator personally fetched the primary source
directly - not through a subagent - and obtained the corrected facts before
the swarm ever ran, specifically so the swarm's own work could be checked
for agreement rather than being the sole source of these facts. After the
swarm finished, the adjudicator personally re-fetched several of its own
highest-stakes new claims again, catching a nuance (see "Restriction list"
below) that neither the swarm's restriction-list specialist nor its
adversarial auditor had fully surfaced.

### The five corrections

**First-turn attack.** The primary source (a page-by-page English
translation of the original 1999 OCG Starter Box rulebook, published by
ygorganization.com after the translator's team acquired an original physical
copy) states explicitly: *"while it's possible to play a Monster Card on the
field on turn 1, it is not possible to attack. Attacking becomes possible
starting from turn 2."* This is now **PROVEN** for the Starter Box, not
ambiguous as the prior gate had it. What remains genuinely unresolved is the
separate question of whether this rule was still in force, unmodified, five
months later at Tokyo Dome - that stays UNKNOWN, and the two questions must
never be conflated.

**Starting Life Points.** The same primary source states: *"Each Duel starts
with each player having 8000 points."* Not 2000 - the prior gate's "probable
2000 LP" was a guess that turned out wrong; 2000 LP belongs to an unrelated
manga/anime "Basic Rules" depiction, not the real tabletop OCG rule. 8000 LP
is PROVEN for the Starter Box; the Tokyo-Dome-specific figure remains a
separate UNKNOWN.

**Deck-out.** The primary source states: *"if either player's Deck is
emptied and said player cannot draw anymore, the outcome of the Duel is
decided by the remaining Life Points... the player with more Life Points at
the moment said player's Deck is emptied wins the Duel."* This is not an
instant loss - it is an LP comparison, confirmed to have remained the rule
through all of Series 1 (i.e. through 1999), with the modern auto-loss
version dated to the later "New Expert Rules" (Series 2, 2000 onward). The
prior gate's "EXACTLY REPRESENTABLE" verdict was wrong: modern ocgcore
hardcodes instant loss on empty-deck draw failure, with no flag or
`OCG_Player` field able to substitute an LP-comparison outcome anywhere in
the complete 36-flag table this repo's own `docs/research/ocgcore-flags.md`
documents. Corrected classification: **NOT_REPRESENTABLE**. This restores
the original, pre-2026-08 hardening gate's own conclusion that deck-out is a
genuine engine gap - the first 2026-08 rules-research pass had incorrectly
overwritten that with "exactly representable," and this pass reverses it.

**Post-battle Main Phase.** The prior gate contained a direct internal
contradiction: one section said `DUEL_NO_MAIN_PHASE_2` removes a legal
historical post-battle action window; another said the historical rules
never had that window at all. The primary source resolves this cleanly:
*"Even when the Battle Phase is over, as long as you do not move to the End
Phase, it remains the Main Phase."* There was no phase called "Main Phase
2" - but action could continue in the single Main Phase after Battle Phase
ended, before the player chose to end their turn. `DUEL_NO_MAIN_PHASE_2`
removes exactly that legal window, which is backwards - this repo's own flag
research already categorizes it as a "variant-format flag (Speed/Rush Duel,
not historical TCG eras)," not a rule-era flag. Correct representation:
leave it unset (**DEFAULT_OMISSION**); the standard MP1→BP→MP2→EP flow
already reproduces the historical substance even though the engine still
internally labels the window "Main Phase 2," a presentational difference no
1999-era card could ever have depended on.

**Hand limit and Tribute Summon.** The prior gate promoted both to PROVEN
"from the original rulebook." Direct re-reading found the rulebook is
silent on both - no hand-size limit or discard rule anywhere, and no
tribute/sacrifice cost for any monster Level, with printed Level-7/8
monsters (e.g. Blue-Eyes White Dragon) already usable for free in the same
March 1999 product. Both are correctly downgraded to **UNKNOWN** at the
Starter Box tier (an absence-based finding, not an under-sourced guess).
Separately and newly established: there is meaningful secondary evidence
that Tribute Summon (Level 5-6 = 1 Tribute, Level 7+ = 2 Tributes, the
modern threshold) was in force generally before Tokyo Dome - but the exact
Expert Rules transition date of **May 5, 1999** remains a **STRONG_
SECONDARY_RECONSTRUCTION, not PROVEN**, for the later-1999 tier (corrected
in a later pass - see "Final hardened research state" below; the earlier
framing on this line, at the time this section was written, overstated it).
The hand-size limit, by contrast, was not introduced until
the later "New Expert Rules" (Series 2, from 2000 onward) - it almost
certainly **postdates Tokyo Dome entirely**, a stronger and more useful
finding than "merely unproven."

### Restriction list - moderately resolved, not fully settled

The restriction-list *content* (Raigeki, Dark Hole, Trap Hole, each Limited
to 1) remains strongly corroborated and undisturbed. The *scope* question -
nationwide OCG vs. tournament-specific vs. modern retrofit - has moved
meaningfully. The adjudicator personally fetched Yugipedia's raw wikitext
and its MediaWiki API revision history directly and confirmed: the page was
renamed and substantively rewritten on **2026-02-22** by editor
SnorlaxMonster, from "July 1999 Forbidden and Limited Lists" (nationwide
framing, sourced only to an archived personal fan webpage whose own title
read "Forbidden/Limited Card Lists **May 15, 2000**" - apparently itself a
retrospective, not a primary July 1999 document) to "August 1999 Lists"
(single-day framing, `start_date = end_date = August 26, 1999`, tied
explicitly to the Tokyo Dome tournament finals, citing a real, page-numbered
2004 Shueisha "Master Guide" book). The editor's own move comment: *"This
list was only used for the Tokyo Dome finals... this is at least more
accurate."* This is Yugipedia correcting itself, on its own initiative, away
from the nationwide/July framing this packet's `banlist.working_id` of
`ocg-1999-07` had provisionally carried forward - that value should now be
read as actively wrong, not merely an unverified placeholder.

A second, Japanese specialist source appeared to independently corroborate
the tournament-specific reading - but personally re-checking it (twice, with
a targeted follow-up query) found the corroboration weaker than the swarm
first reported: the claim is not that source's own primary research, but a
citation of yet a third external site, explicitly presented as "one
hypothesis among three possibilities," with its supporting magazine
reference supplied by an anonymous blog commenter rather than the author's
own verified read. This downgrade is the adjudicator's own catch, not
something either the restriction-list specialist or the adversarial auditor
surfaced. **Net verdict: moderately resolved, not BLOCKED and not fully
settled** - anchored by one genuinely solid citation (Yugipedia's
self-correction) plus one weak, hedged, third-hand corroboration. Do not
canonicalize a restriction list on this basis, but do not continue reporting
it as fully blocked either.

### A striking new finding: the Exodia win condition was unreachable until Tokyo Dome itself

Personally cross-verified by the adjudicator against two independent
Yugipedia pages: **Exodia the Forbidden One** - the fifth and final
Forbidden One piece, without which the textually-PROVEN "assemble all five
in hand" win condition was categorically impossible - was not available in
Japan at all before **August 26, 1999**, when it was first printed in the
"Premium Pack (Japanese)" product distributed at the Tokyo Dome event
itself. Even the other four pieces were only completed as a printable set by
August 5, 1999, three weeks before the event. The Exodia win was, in other
words, unreachable in real OCG play until the exact date this proposed
format is named for - and even then, only for a small, chaotic subset of
attendees, given the venue-exclusive pack's sales were suspended and then
cancelled after roughly two hours amid a crowd that vastly exceeded the
Dome's capacity (Konami's own cited figures: ~55,000 admitted plus 10,000+
turned away, against ~50,000 capacity). This does not change the certified
pre-event pool recommendation - Exodia the Forbidden One correctly remains
outside the 370-card 1999-08-25 pool - but it is important context for any
future decision about event-day card legality.

### Re-derived architecture verdict

**BLOCKED_BY_BOTH** - unchanged as a top-line label, but re-derived rather
than preserved by default, per the task's explicit instruction not to keep
a verdict merely because the prior packet had it. Historically: every rule
area's Tokyo-Dome-tier evidence status is UNKNOWN except deck-out and hand
limit (BOUNDED) and Tribute Summon (AMBIGUOUS) - even after this pass's
substantial strengthening of the Starter-Box and later-1999 tiers, the
event-tier column that actually matters for a Tokyo Dome format specifically
remains almost entirely unresolved. Architecturally: deck-out's LP
comparison, the chain/Spell-Speed model, and the ATK<DEF battle "recoil"
quirk all have no representable engine mechanism, independent of any
Tokyo-Dome-specific applicability question - these are genuine blockers on
their own historical-evidence merits. Notably, the prior pass reached the
same top-line verdict while simultaneously misclassifying deck-out as
exactly representable - an internally false premise that happened not to
change the conclusion, since other genuine blockers (the chain/priority gap)
were already present. This pass's verdict rests on the corrected evidence
matrix throughout and no longer contains that false premise.

No canonical Tokyo Dome format, banlist, pool, rule profile, or lflist was
created by this corrective pass. The certified 370-card pool, its digest,
the 19-product release ledger, and the absence of the fabricated February
1999 National Tournament product were all re-verified live against current
repo state and remain unchanged.

## Final hardened research state (2026-08, third pass)

This is the current, authoritative narrative. Its structured counterpart is
`tokyo_dome_research_current` in
`docs/research/yugi-kaiba-format-source-packet.json` - that JSON key is the
single current, machine-readable source of truth; nothing calling itself
"current" exists anywhere else in the packet. Everything superseded now
lives under the packet's `superseded_findings` key, unmistakably archival.

**Why this pass exists.** Independent review found the packet, as it stood,
contained competing truths: an older rejected section sat side by side with
a later corrective section, and a naive consumer would need to read prose
("this section supersedes that one") to know which structured facts were
authoritative. That is fixed structurally now, not just narratively - the
rejected section was moved wholesale into an archival namespace, and the
corrective section was promoted and renamed to be the sole current
structure. Two further calibration problems were also fixed: the May 5,
1999 Expert Rules date was overstated, and the restriction list's research
confidence and its canonicalization readiness were conflated into one field
when they are genuinely different questions.

### Expert Rules date - recalibrated (SUPERSEDED BY THE 2026-08-29 PRIMARY-SOURCE FIND BELOW)

> **This subsection is now factually superseded, not merely re-labeled.**
> Its central claim - "no source anywhere in this research chain... has
> actually read that book's own content" - was true when written and is
> **false now**: the "Official Guide Starter Book" has since been located
> and personally inspected directly on archive.org (see "Primary-source
> resolution pass: 2026-08-29" below, and
> `primary_source_resolution_2026_08_29.expert_rules_primary_material` in
> the packet). The book's Expert Rules chapter is now PROVEN to directly
> document all three rule changes. What remains unresolved - the exact
> normative effective date, and Tokyo-Dome-specific adoption - is narrower
> than what this paragraph describes and is stated precisely below. Kept
> here, unedited otherwise, as a record of what was known and unknown
> before that discovery.

The prior pass implied "reasonable confidence" for 1999-05-05 as the Expert
Rules effective date. Personally re-verified this session: a book called
the "Official Guide Starter Book" was indeed published on that date -
independently confirmed by a fourth source (ocg-card.com's own product
page, personally fetched this session, agreeing with Yugipedia and two
yugioh-history.com articles). But no source anywhere in this research
chain, across three sessions, has actually read that book's own content
confirming it announces Expert Rules or Tribute Summon - ocg-card.com's
description lists only "duelist essentials, deck collection, duel
terminology dictionary," and the Japanese specialist historian who
investigates this most carefully writes, in their own words: *"I have not
been able to determine the original information source... if my memory is
correct, they should have been documented in the Official Guide Starter
Book, but I do not have the material on hand and cannot verify this."* Three
distinct claims are now held separately rather than as one: (i) confidence
Tribute Summon and related changes happened *at some point* before Tokyo
Dome - MODERATE; (ii) confidence 1999-05-05 is the *exact* effective date -
LOW; (iii) confidence these rules were *enforced at Tokyo Dome specifically*
- UNKNOWN. The evidence matrix now labels this **STRONG_SECONDARY_
RECONSTRUCTION**, a new status distinct from PROVEN/BOUNDED/AMBIGUOUS/
UNKNOWN, reserved for exactly this situation: a claim resting entirely on
secondary sources that may share an unverified common origin.

### Master Guide page 84 - actually inspected, not just cited

The prior pass noted nobody had read the book Yugipedia cites for the
restriction list's scope (Shueisha's *Master Guide*, ISBN 4-08-782089-0,
page 84). This session, the adjudicator discovered that Yugipedia's own
citation links an uploaded scan of the actual page
(`Media:Master Guide p84.jpg`), resolved its direct image URL via the
MediaWiki API, downloaded it, confirmed the downloaded file's size and
pixel dimensions matched the API's own metadata exactly, and personally
viewed it. The page is real, is headed "DECK BEST SELECTION" covering
"1999年2月〜8月" (February-August 1999), and carries its own boxed section
titled **"1999年8月26日大会限定 制限・禁止カード一覧"** - "August 26, 1999
tournament-limited restriction/forbidden card list" - directly above the
three cards (Raigeki, Dark Hole, Trap Hole, each Limited to 1; 0 Forbidden;
0 Semi-Limited). This is a direct, personally-read confirmation that
Yugipedia's citation says what Yugipedia claims - not just that the
citation is real and checkable, but that its content actually supports the
claim. A genuinely new finding, not previously known to this research
chain: the same page states Trap Hole's restriction was lifted again
shortly after ("落とし穴は、すぐに制限が解除されている"). This is recorded as
additional chronology/context, not as independent proof of scope - a
restriction being lifted again soon after is compatible with several
explanations (a one-off tournament rule, a quickly-corrected nationwide
overreach, ordinary early banlist churn), so it does not by itself confirm
the tournament-specific reading. The header text quoted above remains the
strongest and primary evidence for that reading. This is still a 2004
Shueisha retrospective, five years after the event - not a contemporaneous
1999 document - so none of it settles the matter, but the header is a real,
verified, load-bearing upgrade to research confidence specifically.

### Restriction list - two questions, two fields

Research confidence and canonicalization readiness are no longer one field.
**Research confidence is now MODERATE-TO-GOOD**, upgraded this session on
the strength of the Master Guide inspection above: the best current
hypothesis is a Tokyo-Dome-tournament-finals-specific restriction, dated
1999-08-26, of exactly those three cards. **Canonicalization readiness
remains explicitly blocking** - a better secondary source is not a primary
source, and nobody in this chain has inspected a contemporaneous 1999
document. Do not read the confidence upgrade as "no longer blocked."
(Terminology note, 2026-08-29: the packet's exact status string for this
field was standardized to `UNRESOLVED_BLOCKING` during the primary-source
consolidation pass, replacing the bare `BLOCKING` used when this paragraph
was written - same substance, one consistent string across the packet.)

Yugipedia's own revision history behind the "August 1999 Lists" page is now
pinned mechanically rather than narratively: revision 3443496 (2017-03-08,
The-Psychid, page created as "July 1999 Forbidden and Limited Lists," citing
only an archived personal fansite whose own title read "...May 15, 2000")
through revision 5830434 (2026-02-22, SnorlaxMonster, moved to "August 1999
Lists," `start_date = end_date = August 26, 1999`, citing the Master Guide
page just discussed) - seven revisions total, each with its exact revision
ID, parent ID, timestamp, user, and comment recorded in the packet.

### Event disruption - relabeled, not weakened

The prior pass's "BOUNDED-to-PROVEN" language overstated the evidentiary
tier for colorful-but-non-load-bearing event-history material. The
underlying finding is unchanged and still strong - high confidence the
event was severely disrupted, based on multiply-corroborating retrospective
accounts - but it is now labeled by explicit tier rather than a label that
sounds stronger than "no period 1999 source was personally inspected"
actually supports.

### Architecture verdict - re-derived, blockers separated by kind (PARTIALLY SUPERSEDED - see 2026-08-29 section below)

> **The specific unconditional-blocker list below is corrected by the
> 2026-08-29 primary-source consolidation.** The primary-source discovery's
> own more careful redo of the evidence matrix found that "no chain/priority
> concept" had been over-classified as PROVEN here from the same source's
> mere silence on the topic (silence is not proof of absence) - it is
> correctly UNKNOWN and is no longer counted as an unconditional engine
> blocker. A narrower, genuinely PROVEN fact (only Trap Cards, not Spell
> Cards, may respond during the Battle Phase) is retained as an unconditional
> blocker instead. See `architecture_verdict_detail` in the packet for the
> current, corrected list. The top-line `BLOCKED_BY_BOTH` label is unchanged.

**BLOCKED_BY_BOTH**, unchanged as a top-line label but re-derived with the
two blocker categories now kept explicitly separate. Historical-evidence
blockers: restriction-list canonicalization, and the fact that almost every
rule area's Tokyo-Dome-tier evidence status is still UNKNOWN even after this
pass's work. Engine-representation blockers, counted only where the
underlying historical behavior is securely known across the whole relevant
window (not merely where a rule's Tokyo-Dome applicability happens to be
unresolved): deck-out's LP-comparison outcome, the fundamental absence of a
chain/priority model, and the ATK<DEF battle-recoil quirk. Tribute Summon's
Starter-Box-era engine gap is explicitly *not* counted as a blocker, per the
task's own reasoning: the later, engine-exact tribute-required state is the
more likely operative rule by Tokyo Dome anyway, so an engine mismatch tied
to a state that probably wasn't in force isn't a real blocker.

No canonical Tokyo Dome format, banlist, pool, rule profile, or lflist was
created by this hardening pass either. Runtime, schemas, and the errata
model were not touched. The certified 370-card pool, its digest, and the
19-product release ledger were re-verified live and remain unchanged.

## Primary-source resolution pass: 2026-08-29

This is the final adjudication for the primary-source gate. The structured
version is `tokyo_dome_research_current.primary_source_resolution_2026_08_29`
in `yugi-kaiba-format-source-packet.json`; that object is the machine-readable
authority for the statuses below.

### Research method and source boundary

Four evidence lanes were kept independent: restriction-list provenance,
contemporaneous Expert Rules material, Tokyo Dome event documentation, and an
adversarial provenance audit. Agent summaries were discovery aids only. The
final adjudicator personally inspected the load-bearing source objects before
promoting any finding.

The decisive new source is the inspectable scan of Shueisha / Studio Hard's
*Official Guide Starter Book*, published 1999-05-05:

`https://archive.org/details/yugioh-official-guide-starter-book-may-05-1999`

Pages 107-109 were personally inspected. The archive item is a later-hosted
scan of the period book; the repository does not claim ownership of the scan
and does not commit copyrighted pages. The catalogue record independently
confirms the 1999-05-05 publication date:

`https://ocg-card.com/latest/ogs/`

The scan's Chapter 3 is headed `エキスパートルール` (Expert Rules). Its
introduction calls these special rules prepared by Konami for advanced
duelists, adds three rules to the official rules, and says that tournaments
*may* adopt them. The inspected pages then directly describe:

- Rule 1: any-number turn use of Magic/Trap cards while in hand, subject to
  the five-card field limit;
- Rule 2: one field Tribute for Level 5-6 monsters and two for Level 7 or
  higher; and
- Rule 3: Fusion materials may be used from the hand.

This proves that the Expert Rules text was documented in a 1999 guide. It does
not prove that 1999-05-05 was the universal effective date, and it does not
prove that the Tokyo Dome event adopted the rules. The exact transition date
therefore remains `STRONG_SECONDARY_RECONSTRUCTION` /
`SUPPORTED_BUT_INCOMPLETE`, not `PROVEN`.

### Restriction-list adjudication

The exact required outcome is **`UNRESOLVED_BLOCKING`**.

The three-card content remains supported: Raigeki, Dark Hole, and Trap Hole,
each Limited to 1. Scope is a separate question. The strongest located scope
wording is the personally inspected 2004 Shueisha *Master Guide* page 84,
surfaced by Yugipedia, whose header reads
`1999年8月26日大会限定 制限・禁止カード一覧` (“August 26, 1999
tournament-limited restriction/forbidden card list”). That is a later
retrospective, not a 1999 event document. The specialist reconstruction that
repeats a tournament-only reading is itself third-hand and hedged. The older
“July 1999 nationwide” framing also lacks an inspectable contemporaneous
Konami source. Context about Trap Hole being lifted shortly afterward is
chronology, not independent scope proof.

| Hypothesis | Current status | Why it cannot be promoted |
| --- | --- | --- |
| H1 — general OCG list | UNRESOLVED | List content is repeated, but no contemporaneous source proves ordinary nationwide scope. |
| H2 — Tokyo Dome/event-only list | UNRESOLVED | The Master Guide wording is specific but five years late; no 1999 event sheet was found. |
| H3 — other tournament-specific scope | UNRESOLVED | Tournament-oriented cataloguing exists, but the affected tournament population is unknown. |
| H4 — retrospective reconstruction | PLAUSIBLE | The surviving web evidence is downstream and divergent; plausibility is not proof. |

Accordingly, the list verdict is not `PROVEN_GENERAL_OCG`,
`PROVEN_TOKYO_DOME_ONLY`, or `PROVEN_TOURNAMENT_SCOPE_OTHER`.

### Timeline and three-layer rule matrix

| Rule area | Starter Box | Later pre-Tokyo-Dome OCG | Tokyo Dome specifically |
| --- | --- | --- | --- |
| Starting LP / hand | `PROVEN`: 8000 LP; 5 cards. | `SUPPORTED_BUT_INCOMPLETE`: no dated change located. | `UNKNOWN`: no event rule sheet. |
| First-turn draw / attack | `PROVEN`: first player skips the initial draw; turn-1 attacks prohibited. | `SUPPORTED_BUT_INCOMPLETE`: continuity is not separately dated. | `UNKNOWN`. |
| Tribute Summon | `UNKNOWN`: no Level-based Tribute rule is stated. | `SUPPORTED_BUT_INCOMPLETE`: Expert Rules pages directly state 1/2 Tributes, but not their effective date. | `UNKNOWN`: “tournaments may adopt” is not adoption evidence. |
| Fusion materials | `PROVEN`: field-only materials. | `SUPPORTED_BUT_INCOMPLETE`: Expert Rules directly permit hand materials, but adoption date is unpinned. | `UNKNOWN`. |
| Spell activation frequency | `PROVEN`: one Magic card per turn. | `SUPPORTED_BUT_INCOMPLETE`: Expert Rules directly document removing the per-turn cap, but not an effective date. | `UNKNOWN`. |
| Trap-only Battle Phase response | `PROVEN`: only Trap Cards usable during Battle Phase. | `SUPPORTED_BUT_INCOMPLETE`, upgraded 2026-08-29 (session 2): independently re-documented verbatim in the same 1999-05-05 guide's Official Rule Reference chapter (a *different* chapter from Expert Rules, which does not touch this rule) - see "Continuity-evidence closure pass" below. | `UNKNOWN`. |
| Chain/Spell-Speed/priority (full system) | `UNKNOWN`: no modern Chain/Spell Speed model is established. | `SUPPORTED_BUT_INCOMPLETE`: Expert Rules changes activation frequency, not a complete timing system. | `UNKNOWN`. |
| Main/Battle/Main | `PROVEN`: Battle is inside Main and Main continues after Battle until End Phase. | `SUPPORTED_BUT_INCOMPLETE`: the date of the later MP1/MP2 terminology split is unknown. | `UNKNOWN`. |
| Hand limit | `UNKNOWN`: no six-card limit/discard rule is stated. | `UNKNOWN`: the inspected Expert pages do not establish one. | `UNKNOWN`. |
| Deck-out | `PROVEN`: compare remaining LP; higher LP wins. | `SUPPORTED_BUT_INCOMPLETE`, upgraded 2026-08-29 (session 2): independently re-documented verbatim in the same 1999-05-05 guide's Official Rule Reference chapter, not merely a later, uncited "Series 1 vs Series 2" reconstruction - see "Continuity-evidence closure pass" below. | `UNKNOWN`. |
| Battle calculation | `PROVEN`: includes the ATK<DEF attacker-recoil result. | `SUPPORTED_BUT_INCOMPLETE`, upgraded 2026-08-29 (session 2): independently re-documented verbatim in the same 1999-05-05 guide's Official Rule Reference chapter, not merely "no dated change located" - see "Continuity-evidence closure pass" below. | `UNKNOWN`. |
| Main / Side / Fusion deck limits | `PROVEN` for the Starter rules' 40-minimum/no-upper-bound main deck, 10-card Side Deck, and separate Fusion Deck. | `SUPPORTED_BUT_INCOMPLETE`: no event-enforcement document. | `UNKNOWN`. |

The complete 21-area matrix, including Field Spell coexistence, priority,
battle-phase structure, and win-condition/card-availability distinctions, is
stored in the packet with one of the required statuses in every cell. No
Tokyo-Dome cell is `PROVEN`.

The timeline is therefore:

1. The original Starter Box rule tier is directly available through the
   traceable period-rulebook transcription.
2. On 1999-05-05, the Official Guide Starter Book demonstrably contained an
   Expert Rules chapter. This is a publication/documentation date, not a
   proven universal transition date.
3. On 1999-08-26, the event-specific rules remain unknown. The contemporary
   *Los Angeles Times* report describes a Konami-sponsored Tokyo Dome event
   centered on the recently released handheld game and a card swap meet; the
   archived Web Japan report likewise describes the software tournament and
   cancellation. Neither names the tabletop OCG rules.

### Engine and schema reassessment

`DUEL_NO_MAIN_PHASE_2` remains rejected. The historical Starter text permits
legal Main actions after Battle and before End Phase. Current default
MP1 → Battle → MP2 behavior preserves that action opportunity; the flag
removes it. The modern label is an approximation of the historical action
sequence, while the no-MP2 flag is behaviorally wrong.

The engine findings are conditional where event history is unknown:

| Area | Current classification | Finding |
| --- | --- | --- |
| Post-battle Main actions | `UNKNOWN_BECAUSE_HISTORY_UNKNOWN` | Default flow is closer; no-MP2 is rejected. |
| Deck-out | `NOT_REPRESENTABLE` | No pinned flag or sanctioned `init.lua` hook converts empty-deck loss into higher-LP victory. |
| Battle calculation | `NOT_REPRESENTABLE` | Current damage handling does not reproduce the historical attacker-recoil result exactly. Adversarial caveat added 2026-08-29 (session 2): the recoil *arithmetic* itself appears unchanged even in modern Yu-Gi-Oh! rules and was not empirically re-verified against the pinned engine this session (checkouts unavailable) - the genuine gap, if any, is more likely the historical single-step, response-window-free damage *procedure*, not the arithmetic result. A future pass with engine access should re-examine this classification's precise scope. |
| Trap-only Battle Phase | `NOT_REPRESENTABLE` | No ocgcore flag restricts Battle-Phase card usage to Trap Cards only (added 2026-08-29, session 2 - this row was previously missing despite the rule area already being counted as a blocker). |
| Tribute / Fusion / timing | `UNKNOWN_BECAUSE_HISTORY_UNKNOWN` | Expert text is real, but event adoption is not established. |
| Deck / Side / Fusion limits | `REPRESENTABLE_WITH_HOST_CONFIG` | Historical unbounded maxima can be recorded as `null`; `[40, 999]` is a documented EDOPro host ceiling, not historical unlimited. |
| LP / first-turn settings | `UNKNOWN_BECAUSE_HISTORY_UNKNOWN` | Starter values are host-representable, but Tokyo Dome selection is not proven. |

The repository's schema/host verdict remains **sufficient with documented
approximations**. No schema change is required for this research state: the
historical model is recorded with a null upper bound and the finite client
ceiling is explicitly labelled as an approximation. This is separate from the
format-level result, which remains `BLOCKED_BY_BOTH`.

### Canonicalization blocker ledger (per-topic, this pass)

> This table mirrors `tokyo_dome_research_current.primary_source_resolution_`
> `2026_08_29.canonicalization_blockers` exactly - it is a supplementary,
> more granular, per-topic breakdown, not a second independent verdict. It
> uses two statuses the older 18-item ledger (mid-document, "Canonicalization
> blocker ledger" under "Explicit engine gaps") does not:
> `HISTORY_RESOLVED_ENGINE_GAP_REMAINS` (the historical fact is established,
> but the engine still cannot reproduce it, so it remains an active blocker,
> NOT a resolved one - deliberately not spelled "RESOLVED" to avoid reading
> as unblocked) and `NONBLOCKING_HOST_CONFIG_APPROXIMATION` (handled by the
> same client/host-config layer every other format in this repository
> already uses). Every row here is consistent with the older ledger and with
> `architecture_verdict_detail`; where the two ledgers describe the same
> underlying fact, they must not be read as disagreeing.

| Item | Status | Reason |
| --- | --- | --- |
| Restriction-list scope | BLOCKING | `UNRESOLVED_BLOCKING`; later Master Guide wording is not contemporaneous proof. |
| Tokyo Dome ruleset | BLOCKING | No inspected event-specific rule document names Starter or Expert Rules. |
| 1999-05-05 effective transition date | UNRESOLVED | The guide publication and Expert Rules content are proven; exact effective date is not. |
| Post-battle Main behavior | UNRESOLVED | Starter behavior is proven, event adoption is not. |
| First-turn draw/attack, LP, hand size | UNRESOLVED | General source and event-specific adoption are separate propositions. |
| Deck-size and Side/Fusion constraints | NONBLOCKING_HOST_CONFIG_APPROXIMATION | Historical shape is documented; not counted as a canonicalization blocker (see host/client layer note above). |
| Deck-out rule | HISTORY_RESOLVED_ENGINE_GAP_REMAINS | Historical LP comparison is documented at Starter Box AND independently re-documented in the same 1999-05-05 guide (session 2, 2026-08-29); pinned core cannot reproduce it - still an active engine blocker. |
| Battle-Phase Trap-only response restriction | HISTORY_RESOLVED_ENGINE_GAP_REMAINS | Documented at Starter Box AND independently re-documented in the same 1999-05-05 guide (session 2, 2026-08-29), distinct from the per-turn activation cap Expert Rules DOES remove; no ocgcore flag reproduces it - still an active engine blocker. |
| Battle-calculation semantics | HISTORY_RESOLVED_ENGINE_GAP_REMAINS | Historical attacker-recoil procedure is documented at Starter Box AND independently re-documented in the same 1999-05-05 guide (session 2, 2026-08-29); current core does not reproduce the historical procedure exactly - still an active engine blocker (see adversarial caveat in "Engine and schema reassessment" above). |
| Engine representability | BLOCKING | Conditional deck-out, Trap-only-response, and battle-calculation mismatches remain. |
| Schema representability | NONBLOCKING_HOST_CONFIG_APPROXIMATION | No schema change was needed (see host/client layer note above). |

Full chain/Spell-Speed/priority is deliberately **not** listed as its own
row here: its Tokyo-Dome-specific historical status is `UNKNOWN`, and per
this pass's own reasoning it is not independently counted as an
unconditional blocker (the narrower, `PROVEN` Battle-Phase Traps-only
restriction, `trap_activation_frequency`, already covers the confirmed
engine-representation gap - see "Current authoritative state" at the top
of this document).

### Final research verdict

Restriction-list verdict: **`UNRESOLVED_BLOCKING`**.

Were Expert Rules proven in force at Tokyo Dome? **No.** The primary guide
proves the rules were documented by 1999-05-05 and even says tournaments may
adopt them; no inspected source bridges that statement to this event.

Architecture verdict: **`BLOCKED_BY_BOTH`** — historical evidence remains
blocking, and the historically established early deck-out, Battle-Phase
Trap-only response, and battle-calculation behaviors remain engine
approximations/gaps. **Re-adjudicated 2026-08-29 (session 2):** all three now
rest on independently-re-documented positive continuity evidence (a second
dated primary source ~113 days before the event, not silence-based
inference) rather than "no evidence of change was found" - see
"Continuity-evidence closure pass" below. The schema is sufficient with
documented host approximations. `DUEL_NO_MAIN_PHASE_2` was rejected. No
canonical Tokyo Dome format or any related canonical artifact was created,
and the OCG release-ledger import was not begun.

The physical documents now required to close the historical gate are specific:

- a contemporaneous 1999 Konami restriction-list notice or tournament
  regulation naming the three cards and their scope; and
- a Tokyo Dome programme, entry/qualifier sheet, organizer rule notice, or
  period Japanese magazine/newspaper report that names the tabletop OCG rules
  used at the event.

If those objects do not survive online, a verifiable scan from a collector,
library, or period archive with clear title/date/page provenance would be the
next acceptable evidence. Repeated modern summaries are not a substitute.

## Continuity-evidence closure pass: 2026-08-29 (session 2)

This pass re-adjudicated whether `deck_out`, `trap_activation_frequency`
(Battle-Phase Trap-only response), and `battle_calculation` are justified as
*unconditional* Tokyo Dome engine blockers, given that the packet's own
`three_column_evidence_matrix` shows all three at `tokyo_dome.status =
UNKNOWN` (21 of 21 rows, no exceptions) while `architecture_verdict_detail`
treated them as unconditional blockers via a principle resembling "PROVEN at
Starter Box + no located evidence of change" - structurally the same
silence-based reasoning the packet had already, correctly, rejected for full
chain/Spell-Speed/priority ("no chain concept" cannot be inferred from a
source's mere silence on the topic). The question: is the continuity
inference for these three *materially different* and justified, or is the
repository applying inconsistent epistemic standards?

### The decisive finding: a second, dated, primary source

The archive.org scan already cited for the Expert Rules chapter
(`official-guide-starter-book-1999-scan`, the 1999-05-05 Shueisha/Studio Hard
*Official Guide Starter Book*) contains a **separate chapter**, not
previously extracted in detail: an "Official Rule Reference" chapter
(公式ルール　リファレンス), printed pages 101-106, explicitly labelled on its
own title page to be read **backward**, from page 106 to page 101
("なおこの章は106ページより逆に読むこと"). It sits immediately before the
Expert Rules chapter (page 107) in the same physical book. Personally
inspected via page image (not OCR alone - the raw DjVu OCR for this book is
poor for Japanese text and was used only to locate candidate pages, never
treated as evidence on its own) on 2026-08-29:

- **p.105** (deck-out): "また、プレイヤーか相手のデッキが先になくなり、どちらかが
  カードを引くことができなくなった場合は、お互いのライフポイントの差で勝負を決定
  します。その場合は、デッキがなくなった時点でのライフポイントの数が多い方を勝利
  とします。" - "Also, if either the player's or the opponent's deck runs out
  first, and either side becomes unable to draw a card, the outcome is
  decided by the difference in Life Points between the two. In that case,
  whichever side has more Life Points at the moment the deck ran out is the
  winner." Verbatim identical to the Starter Box rulebook.
- **p.104** (Trap-only Battle Phase): "なお、バトルフェイズ中は、フィールドに
  出ている罠カード以外の魔法カードを使うことができません。" - "Note: during
  the Battle Phase, you cannot use Magic Cards other than Trap Cards that are
  on the field." Verbatim identical to the Starter Box rulebook's "Spell
  Cards placed on the field other than Trap Cards cannot be used during the
  Battle Phase."
- **pp.103-104** (battle calculation): the full ATK-vs-ATK and ATK-vs-DEF
  damage table, including "自分の攻撃力＜敵の守備力" ("Your ATK < Enemy's
  DEF"): "...どちらのモンスターもダメージに影響はありません。そのとき「攻撃を
  受けたモンスターの守備力」から「攻撃を仕掛けたモンスターの攻撃力」を引いた
  数値が、攻撃を仕掛けたプレイヤーのライフポイントから引かれます。" - "...neither
  monster is damaged. At that time, the value obtained by subtracting the
  attacking monster's ATK from the enemy's DEF is deducted from the
  ATTACKING PLAYER's Life Points." The attacker-recoil result, unchanged from
  the Starter Box.

This is **not** an absence-of-evidence inference. It is a second,
independently-dated, personally-inspected primary source that *affirmatively
restates* each rule, published the same day as the Expert Rules chapter -
and Expert Rules (in the same book) is confirmed to document only three
changes (Tribute Summon, removing the one-Spell/one-Trap-per-turn activation
cap, and hand-based Fusion materials), none of which touch deck-out,
Battle-Phase card-type restrictions, or battle-calculation. The gap this
narrows is Starter Box (1999-02-04) to Tokyo Dome (1999-08-26); the new
source sits at 1999-05-05, ~113 days (about 3.7 months) before the event,
not at the start of that window.

This finding is recorded structurally in the packet at
`tokyo_dome_research_current.positive_continuity_evidence`, distinct from
(and cross-referenced by) the matrix's own `later_pre_tokyo_dome` tier, which
remains `SUPPORTED_BUT_INCOMPLETE` for all three - **not** silently promoted
to `PROVEN` - because the residual ~113-day gap to the event itself remains
genuinely undocumented.

### Externally-corroborated upper bounds

Independent research (web search, personally spot-checked) found, for two of
the three, when the rule *eventually* did change - always well after Tokyo
Dome:

- **Deck-out**: the Japanese Yu-Gi-Oh Wiki (three separate pages) and
  yugioh-history.com (independently authored, no cross-citation between the
  two) both state the LP-comparison rule held until the "New Expert Rule"
  accompanying the "Magic Ruler" booster's release, **2000-04-20** - about
  8 months after Tokyo Dome. One wiki page cites this to the rule card
  packaged with Booster R1 (a print source, not independently viewable in
  this pass).
- **Trap-only Battle Phase**: Quick-Play Spell Cards (速攻魔法) - the first
  OCG mechanism permitting a Spell/Magic card to be used during the Battle
  Phase - were introduced in the same "Magic Ruler" booster, confirmed via
  Konami's own Yu-Gi-Oh! Neuron card database listing (release date
  2000-04-20).
- **Battle calculation**: no source was found documenting the ATK/DEF
  recoil arithmetic ever changing at all; what is documented is a later
  formalization of Damage Step *timing* (Master Rule 3, 2014-03-21), a
  different axis from the arithmetic result. See the adversarial engine-
  representability caveat below.

### A counter-claim, checked and rejected

A 2024 tweet by manga staff member Ito Akira (@Vg_akira, verified account;
personally fetched and confirmed 2026-08-29) recalls that "at the time" (the
period a Studio Dice manga arc was written, published April 2000) the OCG
deck-out rule was a "draw," not LP-comparison. This directly contradicts
*both* personally-inspected primary documents (the Feb 1999 rulebook and
this May 1999 guide) and is corroborated by no other source in this
research chain - it is recorded in `personally_reverified_claims` for
transparency, explicitly marked considered-and-rejected, not as evidence
against continuity. A decades-later recollection of a casual writers'-room
conversation does not outweigh two independently-dated contemporaneous
documents that agree with each other.

### Tokyo-Dome-specific rules material: still not found

A tightly-scoped search for the event's own tabletop ruleset (programme,
rule sheet, tournament regulations, contemporary press coverage naming the
rules used) found nothing usable - some promising leads (a claimed V Jump
September 1999 write-up, cited only by unreachable third-party pages) could
not be verified and are not treated as evidence either way. This does not
change the adjudication above; it means the `tokyo_dome` tier of the matrix
correctly remains `UNKNOWN` for all 21 rule areas, including these three -
the case for retaining them as blockers rests entirely on the bounded-
continuity reasoning above, not on any event-specific document.

### Adversarial engine-representability caveat

The pinned ocgcore checkouts required to empirically test engine behavior
are unavailable in this environment (all `tests/engine/*` tests skip here).
This pass could not personally verify whether the ATK/DEF recoil
*arithmetic* is actually unrepresentable by the pinned engine - independent
research found no evidence that arithmetic has ever changed, even into
modern rules, which raises the possibility that the genuine engine gap (if
any) is narrower than currently described - more likely the historical
single-step, no-response-window damage *procedure* than the recoil result
itself. The `battle_calculation` classification is left unchanged pending a
future pass with engine access, per this repository's standing rule against
promoting an unverified claim to fact.

### Adversarial review

An independent reviewer was asked to argue against retaining each of the
three behaviours as an unconditional blocker (`positive_continuity_evidence.`
`adversarial_review_2026_08_29` in the packet). Its strongest finding: the
upper-bound evidence for deck-out ("New Expert Rule") and for the Trap-only
restriction (Quick-Play Spell Cards) both trace to the same "Magic Ruler"
release (2000-04-20) - they are recorded as sharing ONE provenance root, not
two independent corroborations, so they are never double-counted. This does
not change either behaviour's core finding, which rests on the May 1999
re-documentation, not the upper bound. The reviewer separately concluded
battle-calculation is the *strongest* of the three on historical-persistence
grounds (no documented change even decades later) and that its real
vulnerability is the unverified engine classification, not the history -
consistent with this pass's own adversarial caveat above.

### Result

All three behaviours survive as unconditional engine blockers, on
materially stronger and more consistent grounds than before. `BLOCKED_BY_BOTH`
is unchanged as the top-line architecture verdict. No canonical Tokyo Dome
artifact was created; the 19-product release ledger, 370-card pool, and
GOAT/Edison/Tengu remain untouched.
