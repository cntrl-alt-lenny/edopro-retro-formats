# Last Will v2 adjudication: c0 historical-model correction

Status: corrected historical decomposition; canonical Last Will remains full
v2. This review covers only `erratum-last-will` (modern passcode `85602018`).
It does not research or alter any other erratum or format.

## Decision

The previous c0 was too strong. TP7 directly establishes the printed-text
retroactivity change, but it does not by itself establish the separate ruling
changes governing deferral or chain procedure. Last Will is therefore modeled
with five independent behavioral events:

| event | question | effective chronology |
| --- | --- | --- |
| `c0` | A: earlier-in-turn send counts (`is sent` → `was sent`) | 2005-11-01, day precision, project TCG release anchor |
| `c1` | B: first qualifying opportunity vs later deferral | old attested through 2005-01-20; new attested from 2006-06-21; exact date unresolved |
| `c2` | C: Chain/trigger procedure vs later no-Chain procedure | old attested through 2005-02-08; new attested from 2006-06-21; exact date unresolved |
| `c3` | D: activation permitted with no eligible Deck target | exact date unresolved |
| `c4` | E: failed-search Deck verification | old attested through 2011-02-02; new attested from 2019-04-03 |

There are no multi-transition events and therefore no authored
`cooccurrence_sources`. The June 2006 material attests B and C together as
then-current behavior, but does not say that their historical transitions were
one act. That is same-source attestation, not proof of co-occurrence.

## Evidence reviewed and source quality

The review reopened:

* the [official Konami Last Will card record](https://www.db.yugioh-card.com/yugiohdb/card_search.action?cid=4885&ope=2), including the current text and listed printings;
* the [official Tournament Pack 7 record](https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&pid=1121204008&request_locale=en&rp=99999), which identifies TP7-EN015 and gives the 2005-11-01 release date;
* the [June 21, 2006 Curtis Schultz article](https://kperovic.com/metagame/yugioh4cb2.html?tabid=33&ArticleId=6095) and [June 28 follow-up](https://kperovic.com/metagame/yugioha1d5.html?tabid=33&ArticleId=6222);
* archived [UDE Specific Card FAQs](https://web.archive.org/web/20070103194937/http://www.upperdeckentertainment.com/yugioh/uk/faq_specific.htm), the archived UDE card-rulings material, later Konami per-set rulings, and the [Netrep 3.0 rulings file](https://www.angelfire.com/anime5/innovation/netrep.pdf);
* the period Ian Estrin, Schultz, Gehrmann, Danker, Roth, and related judge/forum material reproduced and linked by [GoatFormat's historical synthesis](https://www.goatformat.com/home/ruling-notice-last-will);
* the pinned Project Ignis [GOAT script](https://raw.githubusercontent.com/ProjectIgnis/CardScripts/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/goat/c504700147.lua), [modern script](https://raw.githubusercontent.com/ProjectIgnis/CardScripts/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c85602018.lua), BabelCDB, release ledger, and repository v2 tests.

Official Konami/UDE material is strongest for printing and general policy.
Period judge-authored material is strong evidence of contemporary
interpretation but is not treated as a printing record. GoatFormat is a later
secondary synthesis: useful for locating and comparing period evidence, not a
substitute for it. Project Ignis establishes implementation behavior only; a
script does not date a ruling. Yugipedia and community forums are discovery
and corroboration sources, not sole proof of an effective date.

Unsuccessful leads remain material: no Last Will-specific official document
was found that dates B, C, or D; no source announces the exact withdrawal date
of E; and no source states that B and E, or B and C, changed together. The
2003 Tournament Card Ruling PDF and archived FAQ material did not resolve
those gaps.

## A: exact TP7 text change

The official database lists TP7-EN015 as Last Will and lists the later text:

> If a monster on your side of the field was sent to your Graveyard this turn,
> you can Special Summon 1 monster with an ATK of 1500 points or less from your
> Deck once during this turn. Then shuffle your Deck.

The pre-TP7 text in the pinned BabelCDB/GOAT record uses `When ... is sent`.
The local release ledger and official product page use 2005-11-01 as the TCG
release anchor. The evidence supports that project-level day-precision anchor,
but it is not asserted here as an independently verified territory-specific
English distribution timestamp.

This wording directly supports A1: a send earlier in the turn can satisfy the
condition. It does not, by itself, prove B or C. Accordingly `c0` contains one
functional transition (`axis: retroactivity`) and has no co-occurrence field.

## B: deferral / usage window

The archived period answer attributed to Ian Estrin around 2005-01-20 says the
state triggers automatically at the next qualifying send and that declining
is the only chance that turn. This is positive OLD evidence before TP7.

Schultz's June 21, 2006 post-errata explanation says the effect need not be
used immediately and may be taken later in the turn; the June 28 examples
illustrate that later-use reading. This is positive NEW evidence after TP7.

The two attestations bound B, but neither dates the transition. The revised
printed sentence may be consistent with later use, but the period ruling
record shows that this was a ruling-layer question and GoatFormat expressly
describes the later interpretation as being codified after TP7. B is therefore
`c1`, not a second transition inside exact-dated `c0`.

## C: chain / trigger procedure

The old procedure is separately attested in period judge material: Schultz's
October 2004 Monster Gate explanation treats Last Will as starting a new
Chain, and the February 8, 2005 period discussion treats its trigger alongside
other Chain effects. This is the conservative OLD bound used for `c2`.

Schultz's June 21, 2006 explanation says using Last Will's Summon does not use
the Chain. That is positive NEW evidence, but it is post-TP7 explanatory
material, not proof that TP7 itself changed this procedure.

The GOAT script's custom `EFFECT_TYPE_TRIGGER_F` and the modern script's
continuous/free-chain structure are consistent with the period distinction.
They are implementation evidence, not chronology evidence. C is consequently
a separate `ruling/chain-procedure` event with bounded chronology.

The period evidence contains both B and C in the same later discussion, but
does not establish that they changed together. No `cooccurrence_sources` are
authored.

## D: activation legality with no eligible target

The pinned GOAT `checkop2` path offers and consumes the opportunity even when
the Deck has no eligible 1500-or-less monster. The modern `spcon`/`activate`
path requires `Duel.IsExistingMatchingCard` before offering it. This proves a
behavioral distinction, not its date. No reliable Last Will-specific source
located by this review dates D or ties it to E, so D remains the separate
undated `c3` event.

## E: failed-search Deck verification

The GOAT path calls `Duel.GoatConfirm(tp, LOCATION_DECK)` after an empty
search; the modern path has no reveal branch. Archived UDE and Konami rulings
positively attest the general failed-search verification procedure through
the 2011-02-02 Storm of Ragnarok compilation. The first located positive
modern no-verification policy is 2019-04-03. The shared TCG chronology is
applied to Last Will because the historical implementation has the exact
failed-search Deck-confirmation branch; the script still does not establish a
ruling date. E remains `c4`, separate from D.

## Ordering

The exact ordering graph is:

```json
{"chains": [["c0", "c4"], ["c1", "c4"], ["c2", "c4"]]}
```

These are all `date-proven` under the frozen formula: each event's first
confirmed NEW date is no later than `c4`'s last confirmed OLD date of
2011-02-02. No edge is authored between c0 and c1/c2: their bounds straddle
the TP7 date in the wrong direction for the proof formula. No edge involves
c3, whose chronology is unknown, and no B/C co-occurrence or narrative order
is inferred. Declaration order remains semantically irrelevant.

## State space and Coverage

Five event nodes with c0, c1, and c2 each required before c4, while c3 is
independent, produce 18 structural down-set states. The authored Coverage is
deliberately sparse:

| event set | meaning | Coverage |
| --- | --- | --- |
| `{}` | pre-c0 behavior, including the historical ruling package | `reuse-upstream`, passcode `504700147`, `goat/c504700147.lua` |
| `{c0}` | TP7 text/retroactivity with the pre-transition ruling package | `known-gap` |
| every other nonterminal reachable set | no independently justified implementation | unauthored → `UNRESOLVED` |
| `{c0,c1,c2,c3,c4}` | all relevant transitions | synthesized `MODERN` |

The old v1 `resulting_implementation` described the TP7 text while retaining
the old ruling package. After splitting c0, that meaning is still exactly
`{c0}`, so the known gap remains there and nowhere else. No new passcode or
Coverage was manufactured. Baseline implementation metadata and the gap
metadata remain preserved separately.

## GOAT and Edison consequences

At GOAT (`2005-04-01`), c0 and c4 are OLD. B and C are inside their evidence
intervals and D is undated, so the candidates are the eight subsets of
`{c1,c2,c3}`. Modern is impossible. Existing policy still selects the exact
historical upstream implementation, passcode `504700147`; GOAT output and
hash remain unchanged at `0x28E9FC02`.

At Edison (`2010-04-24`), c0, c1, and c2 are NEW, c4 is still positively OLD,
and c3 remains unknown. The candidates are `{c0,c1,c2}` and
`{c0,c1,c2,c3}`. Modern is impossible; both candidates are unauthored and
the format's documented fallback still selects the modern executable card.
The diagnostic remains the intentional
`format.erratum-modern-known-wrong` refinement. Edison output is unchanged
and its pool remains 3673.

## Adversarial review

The correction was checked against the plausible wrong models: merging B into
TP7, merging C into B because both are discussed in June 2006, using scripts
as dates, copying Insect Imitation's decomposition, ordering by the v1 array,
dropping c1/c2/c3 states, and assigning Coverage to an unauthored combination.
Dedicated tests reject unsupported ordering, require the five named events,
pin all 18 down-sets, and assert that only `{}` and `{c0}` are authored.

The remaining unknowns are exact effective dates for B, C, and D, the exact
withdrawal date for E, and the relative ordering of D against the other
events. Those unknowns are representable in v2 and are intentionally not
guessed.
