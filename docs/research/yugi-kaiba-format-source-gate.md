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
| Region | OCG Japan (`ocg-jp`) |
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
the primary rules evidence available in this repository's research packet.
It records 8,000 LP, a minimum-40-card deck with no upper bound, a 10-card
side deck, a five-card opening hand, one draw per turn, no first-turn draw,
no first-turn attack, no hand limit, and no Main Phase 2. It also records the
early deck-out rule: when a player cannot draw, the player with more LP wins.

The same rulebook describes one monster, one Spell, and one Trap per turn,
early battle calculations, a single Field Card, and Fusion materials on the
field. Later Expert Rules material is secondary but consistently reports
that the Expert Rules introduced tribute requirements for Level 5+ monsters,
allowed multiple Spell/Trap activations, and allowed Fusion materials from
the hand. The exact primary publication and effective boundary for Expert
Rules remain unresolved.

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
them at `1999-08-25` using `ocg-jp` scope produces this accounting:

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

An explicit modern unresolved policy would select 79 determinate historical
substitutions and leave the 150 ambiguous records on modern only as a
documented approximation. That policy cannot certify the format: 46 of those
ambiguous records have no historically valid modern possibility, and 47
records contain unresolved candidate coverage. No early-format overrides are
therefore proposed by this gate.

## Architecture decision

No runtime or schema change is required for the research recommendation.
Existing structures are sufficient to describe:

- `ocg-jp` territory scope and a dated release-cutoff pool;
- 40-to-unbounded Main Deck, 0-to-unbounded Extra Deck, and 10-card Side
  Deck limits;
- an explicit historical banlist record once its date and scope are resolved;
- a custom rule profile with documented flags and `known_gaps`;
- fail-safe V2 errata selection that keeps ambiguity visible.

The next implementation may add OCG product/card data and format-local
research artifacts, but it must not change the shared validator or silently
reinterpret the 296 errata. The proposed canonical format remains blocked
until the product ledger, banlist scope, Expert Rules boundary, and early
engine gaps have an evidence-backed implementation decision.

## Source hierarchy

The companion JSON packet records URLs, evidence labels, short notes, and
the exact audit counts consumed by the tests. Primary Konami product/event
pages outrank community databases. The original-rulebook transcription is
used for historical text but is clearly labelled as a later transcription of
the scan. Format Library, YGOPRODeck, and historical-format sites are
cross-checks only. Unresolved conflicts remain unresolved.
