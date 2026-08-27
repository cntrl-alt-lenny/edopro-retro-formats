# Last Will v2 adjudication

Status: migrated to full v2 after manual review on 2026-08-27.

This dossier covers only `erratum-last-will` (modern passcode `85602018`).
It does not research or alter any other remaining format work.

## Decision

Last Will can be represented truthfully as three implementation-relevant
events:

| id | historical question | chronology |
| --- | --- | --- |
| `c0` | TP7 retroactivity and usage-window text revision | 2005-11-01 project TCG release anchor |
| `c1` | activation/use permitted with no eligible Deck monster | exact date unresolved |
| `c2` | failed-search Deck verification | old attested through 2011-02-02; new first located 2019-04-03 |

`c0` contains two functional transitions because the same printed TP7 text
revision changes both the retroactive condition and the time at which the
available Special Summon may be used. Its `cooccurrence_sources` record that
same-event claim. `c1` and `c2` are separate ruling events: one controls
whether the opportunity is offered and consumed, while the other controls
information revealed after a search fails. No source located establishes that
they changed together, so there is no co-occurrence claim or ordering edge
between them.

The only ordering edge is `c0 -> c2`, represented as a date-proven chain.
The TP7 event has a confirmed new date of 2005-11-01 and the old verification
procedure is positively attested through 2011-02-02. There is no authored edge
to or from `c1`, and no edge between `c1` and `c2`.

## Research performed and source quality

The review examined:

* the current official [Konami TCG card database entry for Last Will](https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=4885&ope=2), including its current text and printing list;
* the official [Tournament Pack 7 card database page](https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=1121204008&request_locale=en&rp=99999), which identifies the product and gives its 11/01/2005 release date;
* the archived UDE card-rulings page and archived Konami per-set rulings used by the repository's shared search-verification interval;
* the period [Duelist Academy: Last Will article](https://kperovic.com/metagame/yugioh4cb2.html?tabid=33&ArticleId=6095) by Curtis Schultz, published June 21, 2006, and its [follow-up examples](https://kperovic.com/metagame/yugioha1d5.html?tabid=33&ArticleId=6222) from June 28, 2006;
* the archived [UDE Specific Card FAQ](https://web.archive.org/web/20070103194937/http://www.upperdeckentertainment.com/yugioh/uk/faq_specific.htm), the [later UDE Last Will FAQ capture](https://web.archive.org/web/20090226121422/http://entertainment.upperdeck.com/yugioh/en/gameplay/faqs/cardfaqs/default.aspx?first=L&last=O), and the [Netrep 3.0 rulings file](https://www.angelfire.com/anime5/innovation/netrep.pdf);
* Yugipedia card-errata and set-lineage pages, the local release ledger, and the pinned Project Ignis BabelCDB/CardScripts implementations.

The official Konami database and archived UDE/Konami documents are the
strongest sources for printing and period policy. The 2006 Schultz articles
are period judge-authored explanatory material and are used as corroboration
for how the revised text was understood, not as a replacement for the
printing record. Project Ignis is implementation evidence: it establishes
what the pinned GOAT and modern scripts do, but not when a ruling changed.
Yugipedia and GoatFormat are secondary lineage/adjudication sources and are
used for discovery and corroboration only.

Unsuccessful leads were also recorded. No Last Will-specific official source
was found that dates the no-valid-target activation transition. No source was
found announcing the withdrawal date of the old failed-search verification
procedure, and no source was found that says activation legality and Deck
verification changed in one package. The 2003 official Tournament Card
Ruling PDF was checked but did not resolve these Last Will questions.

## TP7 text and printing chronology

The official database lists `TP7-EN015` as Last Will, gives Tournament Pack 7
the release date 2005-11-01, and shows the later text:

> If a monster on your side of the field was sent to your Graveyard this turn,
> you can Special Summon 1 monster with an ATK of 1500 points or less from your
> Deck once during this turn. Then shuffle your Deck.

The local release ledger uses the same project-level TCG date. The database
and set record establish the printing/date anchor, while the card-errata
lineage identifies TP7-EN015 as the first listed TCG printing with this text.
The available evidence supports day precision for the project's TCG release
anchor; it should not be read as a separately proven territory-specific
English distribution timestamp.

The June 21, 2006 Schultz article quotes the TP7 text and contrasts it with
the old `is sent` wording. It states that the revised condition can be
satisfied by a monster sent earlier in the turn, before Last Will was played.
The same article says the effect can be used at almost any time during the
turn after the condition is satisfied. The June 28 follow-up gives examples
of activating Last Will after an earlier send and of waiting until a later
phase to use it. Together with the text lineage, this is sufficient evidence
that A1 and A2 are consequences of one TP7 text revision, not two separately
dated historical acts.

## Implementation evidence

The pinned GOAT implementation is
`goat/c504700147.lua`. It registers a forward-looking `EVENT_TO_GRAVE`
watcher when Last Will resolves, raises a custom event at the qualifying send,
and resets the effect before the yes/no prompt. Thus the old implementation
does not use a send that preceded resolution, and declining the trigger spends
the opportunity.

The pinned modern implementation is `official/c85602018.lua`. It uses a
global turn flag for an earlier send and a once-per-turn free-chain effect,
which permits the action at a later legal point in the turn. These are two
distinct semantic axes, but the TP7 text and the period explanation tie them
to the same revision event.

The GOAT script also permits the opportunity to be consumed without first
finding an eligible 1500-or-less monster in the Deck and calls
`Duel.GoatConfirm(tp, LOCATION_DECK)` when the search returns empty. The
modern script checks `Duel.IsExistingMatchingCard` before offering the
opportunity and has no Deck-reveal branch. This proves the B and C behavioral
distinction. It does not prove their chronology or co-occurrence.

## Activation legality and failed-search verification

The archived UDE material confirms the old TCG search procedure: a selected
Deck card was shown, and when no eligible card existed the opponent could see
the Deck to verify the failed search. The archived Konami Machina Mayhem
rulings compiled 2010-04-06 and Storm of Ragnarok rulings compiled 2011-02-02
continue to positively attest the same ruling-layer practice. The first
located positive attestation of the modern no-verification policy is the
archived KDE policy capture from 2019-04-03. The withdrawal date therefore
remains an open interval.

That general procedure applies to Last Will as a Deck search because its
historical implementation has the exact `Duel.GoatConfirm` failed-search
branch. This is an implementation-backed application of the general policy,
not a claim that a Last Will script date is a ruling date.

The no-valid-target activation rule is different. It is a legality gate before
the Deck search; failed-search verification is a resolution-time information
procedure after the search. The review found no dated Last Will-specific
ruling for the legality gate, no source saying it changed with verification,
and no basis for deriving an order from the two scripts or from the old v1
array. `c1` is therefore explicitly undated and independent of `c2`.

## Event model and ordering

| event | transitions | effective block | ordering evidence |
| --- | --- | --- | --- |
| `c0` | `functional/retroactivity`; `functional/usage-window` | 2005-11-01, day, reported | TP7 printing/text; co-occurrence sourced by text lineage and the period explanation |
| `c1` | `ruling/search-activation-legality` | date `null`; Last Will-specific date not located | none |
| `c2` | `ruling/search-reveal-procedure` | date `null`; old through 2011-02-02, new from 2019-04-03 | shared period verification evidence |

The JSON uses `ordering.chains: [["c0", "c2"]]`. This passes the frozen
ordering proof because `first_confirmed_new(c0) = 2005-11-01` is no later than
`last_confirmed_old(c2) = 2011-02-02`. Every other pair is left unordered:
the c0/c1 relationship lacks a date or direct source, and B/C have no sourced
co-occurrence or relative chronology. This is intentional absence of a
constraint, not an omitted field or implied declaration order.

## State space and Coverage

The graph has six structural states:

| event set | interpretation | Coverage |
| --- | --- | --- |
| `{}` | old text behavior, old activation legality, old verification | `reuse-upstream`, passcode 504700147, `goat/c504700147.lua` |
| `{c0}` | TP7 text behavior with old ruling package | `known-gap` |
| `{c1}` | activation legality changed alone | unauthored → `UNRESOLVED` |
| `{c0,c1}` | TP7 text plus activation legality | unauthored → `UNRESOLVED` |
| `{c0,c2}` | TP7 text plus verification change | unauthored → `UNRESOLVED` |
| `{c0,c1,c2}` | all relevant events | synthesized `MODERN` |

The existing v1 intermediate `resulting_implementation` describes the TP7
text on top of the old ruling package, so it maps only to `{c0}` and remains a
known gap. No implementation was assigned to any newly reachable combination.
The baseline implementation metadata and the intermediate gap metadata are
preserved separately from Coverage. No guessed state or passcode was added.

## GOAT and Edison consequences

At GOAT (`2005-04-01`), `c0` is OLD and `c2` is OLD; the undated `c1` is
ambiguous. The candidates are `{}` and `{c1}`. The modern terminal state is
not possible. The existing selection policy chooses the exact historical
upstream implementation `504700147`; the unresolved `{c1}` candidate does
not change the generated GOAT output or hash `0x28E9FC02`.

At Edison (`2010-04-24`), `c0` is NEW and `c2` is still positively OLD; `c1`
is ambiguous. The candidates are `{c0}` and `{c0,c1}`. Modern is impossible.
`{c0}` is the documented known gap, so the existing format fallback keeps the
modern executable card/output. The validator diagnostic becomes the accurate
`format.erratum-modern-known-wrong` warning in place of
`format.erratum-unresolved-defaulted`; this is the expected Last Will-specific
diagnostic refinement, not executable output drift. Edison retains pool size
3673.

## Adversarial review and unresolved facts

The review specifically checked that:

* the GOAT script was not used as chronology evidence;
* A1/A2 were not split or ordered merely because they are separate axes;
* B was not inferred from the verification policy;
* B/C were not merged from their co-occurrence in one script;
* TP7 text chronology was not copied from Insect Imitation;
* no v1 `changes[]` position was treated as chronology;
* no new combination received guessed Coverage;
* the known upstream identity and intermediate gap were retained; and
* the output and warning consequences were tested against a repository with
  Last Will restored from the frozen pre-migration fixture, rather than
  comparing the migrated record with itself.

The remaining unknowns are the exact effective date of `c1`, the exact
withdrawal date of `c2` inside its bounded interval, and the relative order of
`c1` and `c2`. None blocks v2: the event distinctions are representable, the
unknown chronology is explicit, and the absent ordering edges preserve the
uncertainty.
