# Failed-search Deck-verification interval — research round 1b

Research date: 2026-09-01. Starting repository SHA:
`54d2e11992c6bc5f5b5c26951d5107dc6cfc347c` (`main`, clean and equal to
`origin/main` before the worker branch was created).

This is a historical-research note only. No canonical data, schema, format,
pool, rules, or generated output was changed.

## Part A: prerelease terminology check

Nothing needed fixing in either scoped document.

- `docs/research/ignis-goat.md` separates the BabelCDB prerelease passcode
  convention (`10ZZYYXXX`, documented in the pinned BabelCDB README) from the
  EDOPro `ot` scope flags. Its scope list identifies `SCOPE_PRERELEASE 0x100`
  in `gframe/data_manager.h`, while its passcode section identifies the
  numeric prerelease convention. The document does not conflate them.
- `docs/research/edopro-data-repos-ui.md` describes `ot` as a bitmask and
  identifies `SCOPE_PRERELEASE 0x100` from the pinned `gframe/data_manager.h`.
  It does not describe `0x100` as a passcode range.

The checks were made against the pinned revisions recorded by the documents'
source entries: EDOPro client `9d6fb3e8417c88008ba1e08b5b7f751cbdba82ac` and
BabelCDB `0659607453a7d79d1adefbfe1ef7477d3c92434c`. No Part A document was
edited.

## Re-derived state and scope

The active brief's inherited `68`/`48` figures do not match the records at
this SHA. Loading all `data/errata/*.json` records through the repository's
`ErratumV2` model and checking the event bounds directly produced:

| format | snapshot | records carrying the exact `2011-02-02` / `2019-04-03` bounds | ambiguous among those records | determinate among those records |
|---|---:|---:|---:|---:|
| `2005-04-goat` | 2005-04-01 | 60 | 40 | 20 |
| `2010-03-edison` | 2010-04-24 | 60 | 40 | 20 |
| `2011-09-tengu` | 2011-09-17 | 60 | 60 | 0 |

There are 296 erratum records in total. The broader model population has 150
ambiguous records at each of the GOAT and Edison dates and 170 at Tengu; the
table intentionally isolates the records carrying this specific shared
verification interval, which is the quantity relevant to this brief.

## Period-source search ledger

The search targeted primary or near-primary period material that could say
which state held on a dated occasion. PDFs were streamed to text and searched
for `verify`, `verification`, failed-search language, and Deck/hand/Extra Deck
checks. Archive HTML was inspected for its linked ruling corpus.

### Existing positive anchors rechecked

- [Machina Mayhem rulings, compiled 2010-04-06](https://web.archive.org/web/20100602051620/http://www.yugioh-card.com/en/gameplay/rulings/10406SDMachinaMayhem_Rules.pdf):
  retains the old procedure for a failed Deck search (“your opponent can ask
  to verify”). This positively establishes OLD eighteen days before Edison.
- [Storm of Ragnarok rulings, dated 2011-02-02](https://web.archive.org/web/20110409070040/http://www.yugioh-card.com:80/en/gameplay/rulings/STOR_Rulebook_20110202.pdf):
  says the opponent may briefly verify when the searched hand summon has no
  legal monster. This is the latest positive old-state anchor found.
- [Starstrike Blast rulings](https://web.archive.org/web/20110902054017/http://www.yugioh-card.com:80/en/gameplay/rulings/STBLRule_101104_ver1.0.pdf)
  and the older [Ancient Prophecy rulings](https://web.archive.org/web/20110902060847/http://www.yugioh-card.com:80/en/gameplay/rulings/ANPR_sneak_ruling.pdf)
  contain old-state Extra Deck verification examples. They corroborate the
  ruling pattern but do not date a transition after Tengu.
- [Stardust Overdrive rulings](https://web.archive.org/web/20110102004742/http://www.yugioh-card.com/en/gameplay/rulings/SOVR_sneak_ruling.pdf)
  and [Crimson Crisis rulings](https://web.archive.org/web/20110102005552/http://www.yugioh-card.com/en/gameplay/rulings/CRMS_sneak_ruling.pdf)
  contain old-state hand-verification examples. They are earlier positive
  attestations, not transition evidence.

### Official per-set ruling corpus enumerated through Wayback CDX

The query was the 2011 capture inventory for
`www.yugioh-card.com/en/gameplay/rulings/*`, filtered to HTTP 200 and
collapsed by URL. The 15 returned PDFs were checked as follows:

- [Starlight Road / Hidden Arsenal / Warriors' Strike / Starter Deck 2009](https://web.archive.org/web/20110102005947/http://www.yugioh-card.com/en/gameplay/rulings/100325DPTin_%20HA_SDWS_ST09_Rules.pdf),
  [Gold Series 3 / Tag Force 5](https://web.archive.org/web/20110102003949/http://www.yugioh-card.com/en/gameplay/rulings/101109%20GoldSeries3_TF5%20Rulings%20-%20x.pdf),
  [Raging Battle](https://web.archive.org/web/20110102005218/http://www.yugioh-card.com/en/gameplay/rulings/RGBT%20Rules%20v1-2.pdf),
  [Extreme Victory](https://web.archive.org/web/20110626063446/http://www.yugioh-card.com:80/en/gameplay/rulings/EXVCRulesBook000512_1.2_x.pdf),
  [Hidden Arsenal 3](https://web.archive.org/web/20110725024218/http://www.yugioh-card.com:80/en/gameplay/rulings/HA03RulesBook110323x.pdf),
  [Duelist Revolution](https://web.archive.org/web/20110712120241/http://www.yugioh-card.com:80/en/gameplay/rulings/DREVRulebook110517_v1.1x.pdf),
  and [The Shining Darkness](https://web.archive.org/web/20110902060515/http://www.yugioh-card.com:80/en/gameplay/rulings/TSHDRulebook_100430.pdf)
  had no general failed-search Deck-verification transition statement in the
  text searched.
- [Absolute Powerforce booklet](https://web.archive.org/web/20110725024153/http://www.yugioh-card.com:80/en/gameplay/rulings/ABPF%20Rules%20Booklet_110512_v1.1x.pdf)
  says that with no open Monster Card Zone the Deck summon cannot happen and
  the opponent cannot check the Deck. This is a specific no-zone resolution
  exception, not a dated general withdrawal of the old failed-search rule.
- [Absolute Powerforce sneak rulings](https://web.archive.org/web/20110102005442/http://www.yugioh-card.com/en/gameplay/rulings/ABPF_sneak_ruling.pdf)
  likewise contain that specific no-zone exception; they do not establish the
  general transition.
- [Ancient Prophecy](https://web.archive.org/web/20110902060847/http://www.yugioh-card.com:80/en/gameplay/rulings/ANPR_sneak_ruling.pdf),
  [Crimson Crisis](https://web.archive.org/web/20110102005552/http://www.yugioh-card.com/en/gameplay/rulings/CRMS_sneak_ruling.pdf),
  [Stardust Overdrive](https://web.archive.org/web/20110102004742/http://www.yugioh-card.com/en/gameplay/rulings/SOVR_sneak_ruling.pdf),
  [Starstrike Blast](https://web.archive.org/web/20110902054017/http://www.yugioh-card.com:80/en/gameplay/rulings/STBLRule_101104_ver1.0.pdf),
  and [Storm of Ragnarok](https://web.archive.org/web/20110409070040/http://www.yugioh-card.com:80/en/gameplay/rulings/STOR_Rulebook_20110202.pdf)
  are the positive old-state documents described above.

The archive query also showed that the official
[`rulings_errata.html`](https://web.archive.org/web/20120807043904/http://www.yugioh-card.com/en/gameplay/rulings_errata.html)
page captured in 2012, 2014, 2015, 2016, and 2018 continued to list the same
2010–2011 ruling PDFs as its card-rulings corpus. The linked
[current errata PDF](https://web.archive.org/web/20120807043904/http://www.yugioh-card.com/en/gameplay/errata/101105%20recent%20errata%20list%20-%20x.pdf)
was also searched; it did not contain a dated failed-search verification
transition.

### Tournament-policy documents

The Wayback CDX inventory for
`www.yugioh-card.com/en/gameplay/penalty_guide/*` was searched, and the
following period documents were inspected:

- [December 13, 2010 policy](https://web.archive.org/web/20110102005855/http://www.yugioh-card.com/en/gameplay/penalty_guide/KDE_TCG_Tournament%20Policy_13Dec10.pdf)
  and [May 5, 2011 policy v1.1](https://web.archive.org/web/20110820040202/http://www.yugioh-card.com/en/gameplay/penalty_guide/KDE_TCG_Tournament_Policy_05May11.pdf)
  cover public knowledge, Deck presentation, and shuffling, but contain no
  failed-search Deck-verification rule.
- [January 2013 policy v1.3](https://web.archive.org/web/20130203103237/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/YGOTournamentPolicy_v1-3_Jan2013.pdf),
  [February 2013 policy](https://web.archive.org/web/20130226131637/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE_TCG_Tournament_Policy_Feb2013.pdf),
  and [November 2013 policy v1.4](https://web.archive.org/web/20131215021346/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE%20TCG%20Tournament%20Policy%20v1.4%202013November14.pdf)
  contain a Card/Hand Verification section. It governs hand disclosure and
  showing a card retrieved by a specific search; it does not state when the
  general failed-search Deck-reveal practice ended.
- [June 2018 policy v1.5](https://web.archive.org/web/20180712131741/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/YGO_Tournament_Policy_v_2018June01.pdf)
  retains the same Card/Hand Verification wording and still does not answer
  the failed-search Deck question. The parallel [KDE-US v1.5 file](https://web.archive.org/web/20180712131639/http://www.yugioh-card.com:80/en/gameplay/penalty_guide/KDE-US_TCG_Tournament_Policy_v2018June01.pdf)
  was also checked; it has no transition statement for this ruling.

The official [KDE-US Tournament Policy v2.2](https://www.yugioh-card.com/en/downloads/penalty_guide/YGOTCG_Policy_v_2_2.pdf)
was also located through the official-site search, and the current
[KDE-US Tournament Policy v2.5](https://www.yugioh-card.com/en/downloads/penalty_guide/YGOTCG_Tournament_Policy_v_2_5.pdf)
was fetched and searched. These modern policy materials contain the explicit
no-verification rule and Mystic Tomato example. Together with the first
located modern archive attestation on 2019-04-03 already recorded in
`data/sources.json`, they corroborate the NEW endpoint but do not provide a
date inside the open period.

## Result

The interval did **not** narrow. The evidence remains:

- OLD positively attested through 2011-02-02, including the hand example in
  the Storm of Ragnarok document;
- NEW first located in the project corpus on 2019-04-03, with the modern
  policy now directly corroborated by KDE-US v2.5;
- no source found that establishes OLD after 2011-09-17, NEW by 2011-09-17,
  or any intermediate transition date.

Accordingly, the Tengu snapshot remains unresolved on the verification axis
under the existing chronology model. This is a failure to find a qualifying
source in the official ruling/policy/archive space searched above. It is not
proof that no such source exists, that no policy change occurred, or that the
change occurred exactly at either endpoint.

## Which axis drives the older GOAT/Edison ambiguity?

Among the 40 exact-bound records that remain ambiguous at both GOAT and
Edison, every record also contains at least one separate event with no usable
date. The missing date is not the verification event. Text inspection of
those events identifies an activation/no-valid-target axis in 39 records; the
remaining record (`Skull Knight #2`) has a separate undated trigger/control
semantics question. The broader shared 38-card cluster already described in
`docs/research/edison-behaviour-gaps.md` is specifically the bundled pair of
undated activation semantics plus dated failed-search verification.

Thus the evidenced answer is: the older snapshot ambiguities are driven by
the non-verification axis, principally the per-card activation-semantics
(fail-to-find/no-target activation) question. The verification axis is OLD
and determinate at both 2005-04-01 and 2010-04-24. No activation chronology
was resolved in this round.

The Pojo/Appendix-A banlist evidence and all `verified` statuses were outside
this brief's permitted changes and were left untouched.
