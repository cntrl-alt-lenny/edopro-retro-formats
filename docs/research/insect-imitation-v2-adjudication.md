# Insect Imitation v2 adjudication

Status: migrated to full v2 after manual review on 2026-08-27.

This dossier covers only `erratum-insect-imitation` (modern passcode
96965364). `erratum-last-will` was not researched or modified.

## Decision

The v2 representation has three separate one-transition events:

| id | question | chronology |
| --- | --- | --- |
| `c0` | RP02 removed face-down Defense Position from the Deck Special Summon | 2009-07-24, day precision |
| `c1` | activation may proceed without an eligible Level+1 Insect in the Deck | exact date unresolved |
| `c2` | a failed Deck search is verified by revealing the Deck | old attested through 2011-02-02; new first located 2019-04-03 |

`c0 -> c2` is the only ordering edge. It is the frozen model's
date-proven relation: the first confirmed new date for `c0` (2009-07-24)
precedes the last confirmed old date for `c2` (2011-02-02). `c1` has no
ordering edge to either event. The JSON declaration order is not evidence.

B and C are separate events, not a co-occurring package. They are different
questions at different points in the operation: B controls whether activation
and Tribute payment are legal; C controls what information is revealed when
resolution finds no card. The GOAT script contains both behaviors, but that is
implementation evidence, not evidence that the historical changes occurred
together. No dated or direct source located in this review establishes
co-occurrence or relative order for B and C, so neither was invented.

## Research performed

The review searched the following evidence classes:

* the pinned Project Ignis GOAT and modern BabelCDB/CardScripts files;
* the official 2003 Tournament Card Ruling PDF, including the Insect
  Imitation entry;
* the archived UDE Card Rulings database and archived Konami per-set rulings
  documents used by the corpus's search-verification interval;
* the current official Konami card database's printing and text lineage;
* Yugipedia's card errata/set pages and the archived contemporaneous ruling
  discussion for the card.

The official 2003 Insect Imitation entry confirms a card-specific restriction
on Special Summoning already-Special-Summoned monsters (using Great Moth and
Larva Moth as examples), but does not answer either B or C. No official
card-specific ruling was found that dates the activation-legality change or
states that it was simultaneous with the verification change. The archived
card discussion at [Forum:Insect Imitation](https://yugioh.fandom.com/wiki/Forum%3AInsect_Imitation)
is later community corroboration only: it records the question and the 2012
statement that the old UDE ruling was no longer official. It is not used as a
precise effective date.

The failed-search procedure is supported by the period official evidence for
the same ruling-layer procedure on Deck searches: the [UDE Card Rulings
capture](http://web.archive.org/web/20050616025109/http://entertainment.upperdeck.com/yugioh/en/faq_card_rulings.aspx),
[Machina Mayhem rulings](http://web.archive.org/web/20100602051620/http://www.yugioh-card.com/en/gameplay/rulings/10406SDMachinaMayhem_Rules.pdf),
and [Storm of Ragnarok rulings](http://web.archive.org/web/20110409070040/http://www.yugioh-card.com/en/gameplay/rulings/STOR_Rulebook_20110202.pdf)
all attest the old verify-on-failed-search practice. The [archived KDE
policy search](https://web.archive.org/web/20190403000000*/yugioh-card.com/en/*policy*)
is the first located source for the modern no-verification rule. Applying
that procedure to Insect Imitation is an implementation-backed inference: the
GOAT operation explicitly calls `Duel.GoatConfirm(tp,LOCATION_DECK)` on a
failed Insect search, while the modern operation has no reveal branch. The
procedure's exact withdrawal date remains unresolved.

Unsuccessful leads included a direct official Insect Imitation ruling for
the no-target activation question, a dated announcement of the general
verification-policy change, and a source directly tying B and C together.
None was located, and the absence is recorded rather than filled by a guess.

## Text and printing chronology

The official Konami card database lists RP02-EN016 as the Retro Pack 2
printing and shows the post-change text without the position clause. The
local release ledger records the TCG-EU release as 2009-07-24 and the
TCG-NA release as 2009-08-04; the canonical `c0` date retains the project's
existing day-precision TCG-EU anchor. The modern database's [Insect Imitation
entry](https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=5131&ope=2&request_locale=en)
also records RP02 as the printing carrying the shortened text. The 2003
official ruling PDF's [Insect Imitation entry](https://ms.yugipedia.com/a/a1/2003_tournament_rulings.pdf)
is older ruling evidence, not evidence for the later printing date.

The pinned GOAT script accepts both face-up Attack and face-down Defense
positions. The modern script accepts face-up only. This establishes the
behavioral meaning of the text change independently of the later ruling
questions.

## Implementation comparison

The historical implementation is preserved as the baseline coverage at
`{}`:

* passcode `504700171`;
* `goat/c504700171.lua`;
* Project Ignis BabelCDB GOAT entry and CardScripts.

That script's target filter omits the modern Deck-existence check and its
operation reveals the Deck on a failed search. The modern script adds the
Deck-existence check and summons face-up without revealing a failed search.
No upstream implementation matches the RP02-only position change while
retaining the old ruling package, so `{c0}` is an explicit `known-gap`.

## State space and Coverage

The ordering graph has six structural relevant-event states:

| event set | meaning | Coverage |
| --- | --- | --- |
| `{}` | old position, old activation, old verification | `reuse-upstream`, 504700171 |
| `{c0}` | RP02 position, old activation, old verification | `known-gap` |
| `{c1}` | newly reachable combination | unauthored -> `UNRESOLVED` |
| `{c0,c1}` | newly reachable combination | unauthored -> `UNRESOLVED` |
| `{c0,c2}` | newly reachable combination | unauthored -> `UNRESOLVED` |
| `{c0,c1,c2}` | all three transitions | synthesized `MODERN` |

No Coverage was authored for the new combinations. The two pre-existing
v1 implementation facts are preserved independently in `states[]` and
`implementation_metadata[]`; metadata is not used to manufacture executable
Coverage.

## GOAT and Edison consequences

At GOAT (2005-04-01), `c0` and `c2` are OLD and `c1` is undated, so the
candidate event sets are `{}` and `{c1}`. The format's existing policy selects
the baseline historical identity 504700171; the `{c1}` candidate remains
unresolved and does not alter the executable output.

At Edison (2010-04-24), `c0` is NEW, `c2` is still positively OLD, and `c1`
is undated. The candidates are `{c0}` and `{c0,c1}`; modern is impossible.
The `{c0}` state is a known gap, so Edison retains its existing modern
fallback/output while the validator's diagnostic improves from the old
unresolved-defaulted classification to the accurate
`format.erratum-modern-known-wrong` finding for this record. This is an
intentional diagnostic refinement, not an executable card-selection change.

The generated GOAT and Edison outputs, hashes, entries, substitution maps,
and Edison pool remain identical before and after the migration.

## Why this migration is justified

The unresolved facts are the exact effective date of B, the exact withdrawal
date of C within its bounded interval, and the relative chronology of B and
C. None prevents truthful representation: v2 supports undated events and
omitted ordering edges. The event decomposition itself is independently
justified by the distinct activation-time and resolution-time behaviors, and
there is no sourced co-occurrence claim to justify merging them. Therefore
the record is migrated to full v2 without a guessed edge, guessed state,
guessed implementation, or new runtime/schema behavior.
