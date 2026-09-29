# Period rulings against the generated scripts (round 035)

**Question.** For each of the sixteen cards this project generated or drafted a
script for (rounds 029, 031, 034), do period TCG rulings support, contradict, or
leave unresolved the one behaviour the script changes from the modern card?

**Status:** research, 2026-09-29. Historical claims in this document rest on the
passages quoted below, each read directly from the capture named. No test run is
evidence for any of them (`AGENTS.md`).

## 1. Result

| # | card | passcode | script's difference from the modern card | GOAT 2005-04-01 | Edison 2010-04-24 | Tengu 2011-09-17 | action |
|---|---|---|---|---|---|---|---|
| 1 | Metalzoa | 600000001 | never revivable after its Deck procedure (strict nomi) | unresolved | **contradicted** | n/a: the erratum (2011-08-13) precedes Tengu | corrected: record reclassified, card removed |
| 2 | Super Vehicroid - Stealth Union | 600000002 | equips only a monster **you** control | n/a: card postdates GOAT | unresolved | n/a: erratum 2011-06-01 precedes Tengu | none; rulings record added |
| 3 | Goddess of Whim | 600000004 | no once-per-turn limit | unresolved | unresolved (a 2008-12 ruling contradicts; range not shown) | unresolved (same) | none; owner list |
| 4 | Strike Ninja | 600000005 | use limit per copy | unresolved | unresolved | unresolved | none; rulings record added |
| 5 | Green Baboon, Defender of the Forest | 600000006 | (a) usable in the Damage Step; (b) no face-up requirement on the destroyed Beast | n/a: card postdates GOAT | (a) **contradicted**; (b) unresolved | (a) **contradicted**; (b) unresolved | (a) corrected in the script; (b) kept, owner list |
| 6 | Rise of the Snake Deity | 600000007 | usable in the Damage Step, so battle destruction triggers it | n/a | **contradicted** | **contradicted** | corrected: record reclassified, card removed |
| 7 | Malefic Blue-Eyes White Dragon | 600000008 | never revivable (strict nomi) | n/a | **contradicted** | **contradicted** | corrected: record reclassified, card removed |
| 8 | Soul Rope | 600000009 | (a) usable in the Damage Step; (b) any cause of destruction, not only a card effect | n/a | (a) **contradicted**; (b) not addressed | (a) **contradicted**; (b) not addressed | (a) record reclassified, script removed; (b) returned to `known-gap` |
| 9 | Gigantes | 600000010 | strict nomi | unresolved | **contradicted** | **contradicted** | not shipped; number retired |
| 10 | The Rock Spirit | 600000011 | strict nomi | unresolved | **contradicted** | **contradicted** | not shipped; number retired |
| 11 | Garuda the Wind Spirit | 600000012 | strict nomi | unresolved | **contradicted** | **contradicted** | not shipped; number retired |
| 12 | VW-Tiger Catapult | 600000013 | strict nomi | n/a | **contradicted** | **contradicted** | not shipped; number retired |
| 13 | Gladiator Beast Heraklinos | 600000014 | strict nomi | n/a | **contradicted** | **contradicted** (the erratum, 2011-10-04, follows Tengu) | not shipped; number retired |
| 14 | Dark Master - Zorc | 600000015 | no once-per-turn limit | unresolved | unresolved (a 2007 Netrep answer contradicts; range not shown) | unresolved (same) | not shipped; owner list |
| 15 | Dice Re-Roll | 600000016 | each copy grants its own re-roll | unresolved | unresolved (a UDE ruling supports; range not shown) | unresolved (same) | not shipped |
| 16 | Second Coin Toss | 600000017 | each copy redoes a toss | unresolved | unresolved (a UDE ruling contradicts; range not shown) | unresolved (same) | not shipped; owner list |

"Contradicted" is used only where a Konami-authored document that was current at
the snapshot says the opposite. Rows marked "range not shown" rest on the UDE card
FAQ and Netrep answers, whose range in force at the snapshots is unresolved for the
whole class (section 5). "n/a" means the record's own chronology puts the erratum
before that snapshot, so the period text is not in force there.

The sections below give the passages. `docs/rounds/035-period-rulings-audit/builder.md`
carries the same table and the action taken.

## 2. What counts as evidence here

- **Konami-authored documents decide.** These are the Konami TCG rulebook, the
  Konami "Current Errata" lists, Konami's per-set card-ruling PDFs, and Konami's
  own TCG strategy site. A document is treated as in force at a snapshot only if a
  capture shows it current at or around that date, or a later capture of the same
  text brackets the snapshot. A capture date is not an effective date, and a page's
  own printed date is a claim, not a proof.
- **UDE card FAQ entries and Netrep answers are period rulings of unshown
  range.** UDE administered the TCG until Konami took over on 2008-12-11 (news
  reports; not read as a primary source here). The card FAQ page was mirrored on
  Konami's own site from 2008-12-15. Section 5 shows how far that can be followed.
- **Yugipedia is a pointer.** `Card_Rulings:<card>` pages were read through the
  MediaWiki API on 2026-09-29 to find the sources. Every claim below was then read
  at the source it points to. Yugipedia lists several UDE rulings with no citation;
  those were found at the UDE/Konami card FAQ instead.
- **OCG rulings are evidence about the OCG.** They are recorded and not counted
  for the TCG.

### Sources read

Captures were retrieved on 2026-09-29 unless stated. All are registered in
`data/sources.json` (ids in brackets).

| id | document | URL (Internet Archive) | capture |
|---|---|---|---|
| `konami-official-rulebook-v71-2010` (existing) | Konami "Official Rulebook Version 7.1" | `web.archive.org/web/20100330231827/http://www.yugioh-card.com:80/en/rulebook/YGO_BegGuide_Ver7-1.pdf` | 2010-03-30 |
| `konami-rulebook-2008-v70` (existing) | Konami rulebook Version 7.0 | `web.archive.org/web/20081230072315/http://www.yugioh-card.com:80/en/gameplay/rulebook/V7_English_Rlbk_lores.pdf` | 2008-12-30 |
| `konami-official-rulebook-v72-2011-dragunity` (existing) | Konami rulebook Version 7.2 | `web.archive.org/web/20110516005009/http://www.yugioh-card.com:80/en/rulebook/EN_Rulebook_lr.pdf` | 2011-05-16 |
| `konami-official-rulebook-v8-2011` | Konami "Official Rulebook Version 8.0" | `web.archive.org/web/20111119172146/http://www.yugioh-card.com/en/rulebook/YGO_RuleBook_EN-v8.pdf` | 2011-11-19; linked as the rulebook from the 2011-09-18 gameplay page below |
| `konami-gameplay-page-2010-03-22` | Konami "Gameplay" page | `web.archive.org/web/20100322204132/http://www.yugioh-card.com/en/gameplay/` | 2010-03-22 |
| `konami-gameplay-page-2011-09-18` | Konami "Gameplay" page | `web.archive.org/web/20110918002333/http://www.yugioh-card.com/en/gameplay/` | 2011-09-18 |
| `konami-errata-list-2009-07-30` | "Current Card Errata List, compiled as of July 30, 2009" | `web.archive.org/web/20091229035333/http://www.yugioh-card.com:80/en/gameplay/errata/YGOErrata090730.pdf` | 2009-12-29 |
| `konami-errata-list-2010-01-05` | "Current Card Errata List, compiled as of January 5, 2010" | `web.archive.org/web/20100331022617/http://www.yugioh-card.com/en/gameplay/errata/YGOErrata100105.pdf` | 2010-03-31 |
| `konami-errata-list-2010-11-05` | "Recent Card Errata List, compiled as of November 5, 2010" | `web.archive.org/web/20101214022808/http://www.yugioh-card.com:80/en/gameplay/errata/101105%20recent%20errata%20list%20-%20x.pdf` | 2010-12-14 |
| `konami-extreme-victory-rulings-2011-05` | "Extreme Victory - Card Rulings, compiled as of May 12, 2011, version 1.2" | `web.archive.org/web/20110918002333/http://www.yugioh-card.com/en/gameplay/rulings/EXVCRulesBook000512_1.2_x.pdf` | 2011-09-18 |
| `konami-tcg-strategy-special-summons-2009` | Konami TCG Strategy Site, "Special Summons - Spotting the Different Kinds" (Gregory Taketa; the page prints "December 7th, 2009") | `web.archive.org/web/20151106193938/https://yugiohblog.konami.com/articles/?p=1099` | 2015-11-06, the earliest capture |
| `konami-card-faq-2008-12-15-de`, `-fh`, `-pr`, `-uz`; `konami-card-faq-2008-12-15-skilled-white-magician` (existing, the `default_st` page) | Konami-hosted per-card FAQ, pages D-E, F-H, P-R, S-T, U-Z | `web.archive.org/web/20081215054617/…/faqs/cardfaqs/default_de.html`, `…054619…default_fh`, `…065604…default_pr`, `…054634…default_st`, `…054635…default_uz` | 2008-12-15 |
| `ude-card-rulings-archive` (existing) | UDE per-card rulings, all letters on one page | `web.archive.org/web/20050701235627/http://entertainment.upperdeck.com/yugioh/en/faq_card_rulings.aspx` | 2005-07-01 |
| `ude-card-faq-2009-02-26-uz` | the same FAQ hosted by UDE, page U-Z | `replay.waybackmachine.org/20090226215920/http://entertainment.upperdeck.com/yugioh/en/gameplay/faqs/cardfaqs/default.aspx?first=U&last=Z` | 2009-02-26; other letters 2009-02-17 to 2009-02-26 |
| `ude-judge-list-zorc-2007` | UDE Judge List, "Dark Master - Zorc : once per turn?" | `web.archive.org/web/20071027075924/entertainment.upperdeck.com/community/forums/thread/883212.aspx` | 2007-10-27 (answer posted 2007-10-11) |
| `ude-judge-list-snake-deity-2007` | UDE Judge List, "Rise of the Snake Deity - Damage Step?" | `web.archive.org/web/20071101080500/http:/entertainment.upperdeck.com/community/forums/thread/830322.aspx` | 2007-11-01 (answer posted 2007-08-17) |
| `ude-judge-list-green-baboon-2007` | UDE Judge List, "Green Baboon ... Vs. face-downs, DNA Surgery" | `web.archive.org/web/20071015170441/http:/entertainment.upperdeck.com/community/forums/thread/859107.aspx` | 2007-10-15 (answer posted 2007-09-28) |
| `yugipedia-card-rulings` | Yugipedia `Card_Rulings:<card>` pages, MediaWiki API | `yugipedia.com/api.php?action=parse&page=Card_Rulings:<card>&prop=wikitext&format=json` | 2026-09-29 |
| `konami-ocg-card-database-faq` | Konami OCG card database Q&A pages (Japanese, current, undated) for Gigantes (cid 5831), Gladiator Beast Heraklinos (7303), Metalzoa (4398), Malefic Blue-Eyes White Dragon (8864) | `www.db.yugioh-card.com/yugiohdb/faq_search.action?ope=4&cid=<n>&request_locale=ja` | 2026-09-29 |

## 3. The class question: "can only be Special Summoned by ..."

**Asked.** In the TCG from 2005 to 2011, could a monster whose text read "This card
cannot be Normal Summoned or Set. This card can only be Special Summoned by ..." be
Special Summoned from the Graveyard by another card's effect once it had been
properly Special Summoned, or did that wording lock it permanently?

**Answer, for 2010 and 2011.** It could be revived. Only the wording "cannot be
Special Summoned **except** by ..." locked a monster permanently. This is what the
generated strict-nomi scripts get wrong. The two wordings were ruled differently by
Konami, and every card in the strict-nomi group below carries "can only be Special
Summoned", never "except".

Passages read:

1. **Konami rulebook, Versions 7.0 (2008-12-30), 7.1 (2010-03-30), 7.2 (2011-05-16) and
   8.0.** The summoning page, under "Special Summon with a Card's Effect", after
   defining "Special Summon Monsters": "You cannot use a card effect to Special Summon
   those monsters from your hand, Deck, or the Graveyard unless it was properly Special
   Summoned first." The sentence, with the same neighbouring text, is present in all
   four captures (searched by phrase in each). It is a general rule: a properly
   Summoned Special Summon Monster is not excluded from later Special Summons by
   another card. It names no exception.
2. **Konami TCG strategy site, "Special Summons - Spotting the Different Kinds",
   printed date December 7th, 2009.** For "This card cannot be Normal Summoned or Set.
   This card can only be Special Summoned by...": "Once you successfully Special Summon
   one of these monsters from your hand, and it goes to the Graveyard, you can use
   cards like "Call of the Haunted" to Special Summon them again from the Graveyard."
   For "This card cannot be Normal Summoned or Set. This card cannot be Special
   Summoned except by...": "Even if you Special Summon one of these monsters properly,
   by following the instructions on the card, you cannot use another card's effect to
   Special Summon it from the Graveyard afterwards." For Contact Fusions ("You do not
   use "Polymerization""): "These monsters follow the same rules as monsters like "Chaos
   Sorcerer" that say "This card can only be Special Summoned by..."". **Caveat:** the
   earliest archive capture is 2015-11-06, so the 2009 date is the page's own
   statement and the 2009 text is not authenticated. The distinction it draws is
   independently attested in items 3 and 4.
3. **Konami "Extreme Victory - Card Rulings", compiled as of May 12, 2011, version
   1.2**, linked from Konami's own Gameplay page as captured 2011-09-18. For Meklord
   Astro Dragon Asterisk (EXVC-EN015), whose text is "This card cannot be Normal
   Summoned or Set. This card can only be Special Summoned by controlling 3 or more
   face-up "Meklord" monsters.": "If you Special Summon this card correctly, it can
   later be Special Summoned back from the Graveyard." This is a card-specific TCG
   ruling on exactly the wording in question, four months before Tengu.
4. **UDE/Konami card FAQ (Konami-hosted 2008-12-15, UDE-hosted 2005-07-01 and
   2009-02-26).** "Dimension Fusion" cannot Special Summon a "Special Summon-only"
   monster, like a Ritual Monster or "Chaos Emperor Dragon - Envoy of the End", unless
   it was properly summoned first" (Chaos Emperor Dragon's text carries "can only be
   Special Summoned by"). "VWXYZ-Dragon Catapult Cannon: Once properly Summoned by the
   method written in the text this card can be Special Summoned from the Graveyard with
   effects like "Call of the Haunted" or "Re-Fusion"" (a contact Fusion sibling of
   VW-Tiger Catapult). Against that, the same FAQ locks cards that say "except": "Berserk
   Dragon ... cannot be Special Summoned EXCEPT by the effect of "A Deal with Dark
   Ruler". So "Berserk Dragon" cannot be Special Summoned with "Monster Reborn", etc.,
   even if Special Summoned properly first" (same for Dark Paladin, Mazera DeVille,
   Mirage Knight, Exodia Necross, Spirit of the Pharaoh) and "Horus the Black Flame
   Dragon LV8 has the word "except" in its Summoning conditions, which means that even if
   Special Summoned properly, you cannot revive it". The XYZ-Dragon Cannon entry ("cannot
   be Special Summoned from the Extra Deck except by the method described in their text
   ... cannot be Special Summoned from the Graveyard even after") also uses "except".
5. **Konami, "Starstrike Blast - Card Rulings", compiled as of November 4, 2010**, shows
   both wordings in print on Konami's own cards ("cannot be Special Summoned except by"
   for Blackwing - Aurora the Northern Lights; "can only be Special Summoned by Fusion
   Summon" for Supreme Arcanite Magician), confirming the two wordings coexisted in the
   2010-2011 texts.

**Range in force.** Item 1 is the same text at 2008-12-30, 2010-03-30 and 2011-05-16
(Version 8.0, linked from Konami's page on 2011-09-18 and captured 2011-11-19), so the
rule is bracketed on both sides of Edison and Tengu. Item 3 is a Konami document dated
before Tengu and listed on the 2011-09-18 page. Item 2 is the only source that states
the "except" boundary in prose from Konami itself, and its date is the page's own
claim; items 4 and 5 show the same boundary in UDE-era rulings and Konami's own 2010
card texts.

**GOAT (2005-04-01): unresolved.** The UDE page captured 2005-07-01, three months after
GOAT, already carries the entries in item 4 (Dimension Fusion and Chaos Emperor Dragon;
Berserk Dragon, Dark Paladin, Mazera DeVille, Mirage Knight, Exodia Necross, Horus LV8
"except" entries; Fusion and Ritual "properly Summoned" entries). A capture date is not
an effective date, and nothing dated before 2005-04-01 was found. Best sources for each
side: for revival, that UDE page and its "Special Summon-only" entries; for a permanent
lock, only the "except" entries, which say nothing about "can only" cards.

**Best sources on the other side (permanent lock for "can only" wording).** None found
for 2005-2011 TCG. The community claim that "Nomi" cards could never return
(`docs/research/edison-behaviour-gaps.md` section 2, from the wording pattern) has no
period TCG source behind it. The Konami OCG database says the four OCG-checked cards
(Gigantes, Heraklinos, Metalzoa, Malefic Blue-Eyes) can be revived after a proper Special
Summon, in Japanese, current and undated: "Special Summon Monsters" pages 5831, 7303,
4398, 8864, e.g. for Gigantes "the Gigantes that was successfully Special Summoned, if
afterwards sent to the Graveyard, can be Special Summoned from the Graveyard by the effect
of Monster Reborn". That is OCG evidence and is recorded, not counted.

## 4. The class question: Damage Step activation

**Answer.** In the TCG at both snapshots, a Normal Trap Card could not be activated in
the Damage Step. Konami rulebook Versions 7.0, 7.1, 7.2 and 8.0 (same captures as
above), "Damage Step Rules", "Limitations on Activating Cards": "During the Damage Step,
you can only activate Counter Trap Cards, or cards with effects that directly change a
monster's ATK or DEF. Also, these cards can only be activated up until the start of
damage calculation." The UDE Netrep's note on the Rise of the Snake Deity thread (section 6, card 6) says any Trap
allowed there is "case-by-case ... a small handful of Trap Cards have been given special
privileges", so a Trap with no such ruling follows the rulebook.

## 5. UDE-era card rulings: range in force is unresolved for the class

Question: whether a UDE card ruling still held at 2010-04-24 or 2011-09-17.

- The per-card FAQ text is unchanged across captures from 2005-07-01 (UDE) through
  2008-12-15 (Konami-hosted) to 2009-02-26 (UDE). The entries used below were compared
  between the Konami-hosted 2008-12-15 pages and the UDE-hosted 2009-02 pages
  (Dark Master - Zorc, Dice Re-Roll, Goddess of Whim, Green Baboon, Heraklinos, Rise of
  the Snake Deity, Second Coin Toss, Strike Ninja, Super Vehicroid - Stealth Union,
  Dimension Fusion, VWXYZ-Dragon Catapult Cannon): identical.
- The archive holds no capture of either host's card FAQ after 2009-02-26 (Internet
  Archive CDX listing: Konami host, last capture 2009-01-19; UDE host, last capture
  2009-02).
- Konami's Gameplay page as captured 2010-03-22 and 2011-09-18 links the errata list, the
  rulebook and per-set ruling PDFs. It does not link the card FAQ.
- Konami did revise at least one FAQ entry: for Green Baboon the FAQ (2008-12-15) says
  the effect "can be activated during the Damage Step", and Konami's errata list of
  2009-07-30 says "You cannot activate the effect of this card during the Damage Step."
  That is a documented case of Konami's later document overriding the UDE-era entry.
- Yugipedia says Konami later deemed these rulings unofficial, citing a Konami Judge
  Program forum thread ("Individual Email Rulings VS Individual Card Rulings"). That
  thread needs a login; its archived copy returned only the login page, so the claim and
  its date are not established here.

**Class answer: unresolved.** The UDE card FAQ was Konami-hosted from 2008-12-15, was
still the text on both hosts in 2009-02, and one entry was superseded by a Konami list in
2009-07. Nothing read shows it still in force in 2010-04 or 2011-09, and nothing read
withdraws it. Every verdict that rests only on the UDE FAQ or a Netrep answer is
therefore "unresolved", with the direction of the ruling stated.

## 6. The cards

Format: implemented difference; sources with passages; verdicts; action.

### 6.1 Metalzoa (600000001)

- **Difference.** The script forbids every Special Summon of Metalzoa except its own
  Deck procedure, so a Metalzoa that has been properly Summoned once can never be revived.
  The modern card ("Must first be Special Summoned") can.
- **Text in force.** "This monster can only be Special Summoned from your Deck to your
  side of the field by offering "Zoa" equipped with "Metalmorph" as a Tribute." It is
  "can only", not "except". It lacks the "cannot be Normal Summoned or Set" sentence;
  the Konami article applies the same rule to Contact Fusions that also lack it, and the
  rulebook rule covers every Special Summon Monster.
- **Sources.** Section 3, items 1-4. Konami OCG database, cid 4398: "After being
  Special Summoned by the method written on the card, if sent to the Graveyard by
  destruction etc., it can be Special Summoned from the Graveyard by the effect of
  "Monster Reborn" etc." (OCG only).
- **Verdicts.** GOAT: unresolved (section 3). Edison: contradicted. Tengu: not
  applicable; the record dates the erratum 2011-08-13 (WP11-EN014), before 2011-09-17.
- **Action (part C).** Erratum classification `functional` to `cosmetic` with the
  ruling as added evidence; generated card removed; number 600000001 retired.

### 6.2 Super Vehicroid - Stealth Union (600000002)

- **Difference.** The equip effect selects only a monster you control; the modern card
  selects any face-up non-Machine monster on the field.
- **Sources.** Konami-hosted card FAQ 2008-12-15, page S-T: "You can equip "Super
  Vehicroid - Stealth Union" with more than 1 monster with its effect. (Although you
  can only activate the equipping effect once per turn)"; "You cannot select a face-down
  monster to equip to "Super Vehicroid - Stealth Union" because a face-down monster's
  Monster Type cannot be determined." Neither addresses whose monster may be chosen. The
  second supports the script's face-up filter, range not shown.
- **Verdicts.** Edison: unresolved (the difference rests on the printed "you control"
  alone). Tengu: not applicable (erratum 2011-06-01). GOAT: not applicable.
- **Action.** None. The rulings record is added.

### 6.3 Goddess of Whim (600000004)

- **Difference.** No use limit; the modern card is "Once per turn".
- **Sources.** Konami-hosted card FAQ 2008-12-15, page F-H (identical on the UDE host
  2009-02-26): ""Goddess of Whim's" effect is an Ignition Effect. It can only be used
  once per turn, during your Main Phase." Not present in the UDE page of 2005-07-01. The
  printed English text (MP1-003, LCYW-EN241 for the errata) carries no limit.
- **Verdicts.** GOAT, Edison, Tengu: unresolved. A ruling contradicts the script; its
  range in force at the snapshots is not shown (section 5).
- **Action.** None. The owner is asked (section 9).

### 6.4 Strike Ninja (600000005)

- **Difference.** The use limit belongs to each copy; the modern card is limited by name.
- **Sources.** UDE page 2005-07-01 and Konami-hosted FAQ 2008-12-15: "You cannot
  activate "Strike Ninja"'s effect during the Damage Step", it is a Quick Effect, needs to
  be face-up, and "Removing 2 DARK monsters for "Strike Ninja"'s effect is a cost." None
  addresses copies. Konami's per-set PDFs read (Gold Series 3, Tag Force 5, Starstrike
  Blast, Extreme Victory) do not either.
- **Verdicts.** GOAT, Edison, Tengu: unresolved (printed text only).
- **Action.** None. The rulings record is added.

### 6.5 Green Baboon, Defender of the Forest (600000006)

- **Difference.** (a) It can be activated in the Damage Step, so battle destruction of a
  Beast triggers it; (b) the destroyed Beast need not have been face-up. The modern card
  has neither.
- **Sources for (a).** Konami "Current Card Errata List", compiled as of 2009-07-30,
  2010-01-05 and 2010-11-05: under "From Retro Pack 2, Dark Legend, and SHONEN JUMP
  Magazine", "Green Baboon, Defender of the Forest", "You cannot activate the effect of
  this card during the Damage Step." The 2010-01-05 list is the one Konami's Gameplay
  page captured 2010-03-22 calls "Current Errata"; the 2010-11-05 list is the one the
  page captured 2011-09-18 calls "Current Errata". The rulebook rule of section 4 says
  the same for any card without a Damage Step ruling of its own. The earlier UDE/Konami
  FAQ says "This effect can be activated during the Damage Step, at the same time as
  effects like "Giant Rat's"" (2008-12-15): a conflict between period sources, resolved
  by order and authorship (Konami's list is later, and is Konami's statement of the text
  to play).
- **Sources for (b).** UDE Netrep, 2007-09-28: "You cannot activate the effect of "Green
  Baboon, Defender of the Forest" in this case" (a Beast destroyed face-down by Torrential
  Tribute or Shield Crash); card FAQ 2008-12-15: "This effect can be activated after a
  Beast-Type monster you control is destroyed and sent to the Graveyard, if that monster
  was face-up ..." and "You cannot activate this effect when a face-down Beast-Type
  monster you control is destroyed by a card effect." Konami's errata lists say nothing on
  face-up either way. Range in force: not shown.
- **Also in the Konami lists.** "you can only Special Summon 1 "Green Baboon, Defender
  of the Forest," even if multiple copies are available in your hand/Graveyard." The
  round's engine check of the script is in section 6.5 of the report.
- **Verdicts.** (a) Edison and Tengu: contradicted. (b) both: unresolved. GOAT: not
  applicable (JUMP-EN014, 2007).
- **Action.** The script is changed to match (a): no activation in the Damage Step.
  (b) is kept as recorded and is on the owner's list. The record carries a contradicting
  finding of unshown range for (b).

### 6.6 Rise of the Snake Deity (600000007)

- **Difference.** The script lets the Trap be activated in the Damage Step, so Vennominon
  destroyed by battle triggers it; the modern card is "except by battle".
- **Sources.** UDE Judge List, asked 2007-08-11 "Can be activated during the Damage Step
  (specifically, when "Vennominon" is destroyed by battle)?", answered by the UDE Netrep
  2007-08-17: ""Rise of the Snake Deity" cannot be activated in the Damage Step." The
  thread's last post (2007-08-31, the post number in Yugipedia's link) adds that these
  cases are "case-by-case". The rulebook rule of section 4 (Versions 7.0-8.0). The
  Konami-hosted card FAQ 2008-12-15 lists no Damage Step exception for this card.
- **Verdicts.** Edison and Tengu: contradicted (Konami rulebook in force at both; the
  Netrep answer agrees). GOAT: not applicable. The erratum (2011-10-04) follows Tengu.
- **Action (part C).** Erratum classification `functional` to `cosmetic`; card removed;
  number 600000007 retired.

### 6.7 Malefic Blue-Eyes White Dragon (600000008)

- **Difference.** Strict nomi: never revivable. The modern card can be revived.
- **Text.** "This card cannot be Normal Summoned or Set. This card can only be Special
  Summoned by removing from play 1 "Blue-Eyes White Dragon" from your Deck." The wording
  the Konami article uses for revivable monsters, sentence for sentence.
- **Sources.** Section 3. Konami OCG database, cid 8864: "After being Special Summoned by
  this method, if sent to the Graveyard, or banished face-up, it can be Special Summoned
  by the effect of another card" (OCG only).
- **Verdicts.** Edison: contradicted (the card's first printing, DPKB-EN023, is days
  before Edison; the rulebook and FAQ rule are earlier). Tengu: contradicted (Konami's
  Extreme Victory ruling for the same wording, 2011-05-12). GOAT: not applicable.
- **Action (part C).** As Metalzoa; number 600000008 retired.

### 6.8 Soul Rope (600000009)

- **Difference.** (a) Activation in the Damage Step, so battle destruction triggers it;
  (b) any destruction, not only destruction by a card effect.
- **Sources for (a).** Section 4 (Konami rulebook Versions 7.0-8.0). Konami OCG FAQ, per
  Yugipedia: "You cannot activate this card during the Damage Step" (OCG only, not
  opened at the source). No TCG ruling found that gives Soul Rope a Damage Step
  privilege. UDE FAQ pages (Feb 2009) and Konami's set rulings have no entry for it.
- **Sources for (b).** None. The 2015 erratum's "by a card effect" is dated 2015-11-12;
  no period ruling addresses it.
- **Verdicts.** (a) Edison and Tengu: contradicted. (b): not addressed at either.
- **Action (part C).** The Damage Step transition (2012-09-29) is reclassified
  `cosmetic`; the generated script is removed; the state that applies at the snapshots
  returns to `known-gap` for the 2015 difference (b), with the ruling cited.

### 6.9 Gigantes, The Rock Spirit, Garuda the Wind Spirit, VW-Tiger Catapult, Gladiator Beast Heraklinos (600000010 to 600000014)

- **Difference.** Strict nomi in all five: never revivable after the printed procedure.
- **Text in force.** All five say "can only be Special Summoned by ..." and none says
  "except": Gigantes "can only be Special Summoned by removing from play 1 EARTH monster
  in your Graveyard"; The Rock Spirit the same; Garuda "can only be Special Summoned by
  removing from play 1 WIND monster in your Graveyard" (Edison-era wording, c0);
  VW-Tiger "can only be Special Summoned from your Extra Deck by removing from play the
  above cards you control. (You do not use "Polymerization")"; Heraklinos "can only be
  Special Summoned from your Extra Deck, by returning the above cards you control to the
  Deck".
- **Sources.** Section 3. For the two Contact Fusions the Konami article and the FAQ
  entry for VWXYZ-Dragon Catapult Cannon speak to the same procedure text.
  Konami OCG database: Gigantes cid 5831 and Heraklinos cid 7303, Yugipedia's Konami OCG
  citations, confirmed at the database (OCG only). VW-Tiger and Heraklinos are not in
  Project Ignis's GOAT list.
- **Verdicts.** GOAT: unresolved for Gigantes, The Rock Spirit and Garuda (all three are
  in the GOAT list as modern codes; the record dates their GOAT-era text); not applicable
  for VW-Tiger Catapult and Heraklinos (printed after GOAT). Edison and Tengu: contradicted.
  Heraklinos's erratum (2011-10-04) follows Tengu; Garuda's, Gigantes's, The Rock
  Spirit's and VW-Tiger's are later.
- **Action (part E).** Not shipped: not `supported`. Numbers 600000010 to 600000014
  stay unassigned and are retired. None of the five exists on `main`, so no data changes
  for them in this round beyond what part D carries.

### 6.10 Dark Master - Zorc (600000015)

- **Difference.** No per-turn limit on rolling; the modern card is "Once per turn".
- **Sources.** UDE Judge List, asked 2007-10-08 "Can you use its effect more than once
  per turn?", answered by the UDE Netrep 2007-10-11: "No. You can only roll the 6-sided
  die once. Ex: If you use the effect during Main Phase 1, you would not be able to use
  it again during Main Phase 2." The card FAQ (2005-07-01, 2008-12-15) says only "you roll
  the die during Main Phase 1 or 2 of your turn only" and that a 6 destroys Zorc too. The
  Japanese first printing (305-029) is transcribed on Yugipedia's `Card_Errata` page with
  "１ターンに１度" ("once per turn"); the printing itself was not opened, so the
  transcription is a pointer and the claim is OCG-side only.
- **Verdicts.** GOAT: unresolved (the Netrep answer, 2007, postdates it). Edison,
  Tengu: unresolved: a ruling contradicts the script; its range is not shown.
- **Action.** Not shipped. The owner is asked.

### 6.11 Dice Re-Roll (600000016)

- **Difference.** Each copy grants its own re-roll; the modern card grants one per
  turn, per player.
- **Sources.** UDE page 2005-07-01, Konami-hosted FAQ 2008-12-15: "You activate "Dice
  Re-Roll" before you activate the effect which will let you roll a die. Then you can
  use the effect of "Dice Re-Roll" once during the turn in which you activated it."
  This is a per-activation reading, which agrees with the script. The same entry says it
  can re-roll an Archfiend's roll and a roll in the Damage Step, and that it negates both
  rolls of "Roulette Barrel"; the script's upstream re-rolls any roll by either player.
- **Verdicts.** GOAT: unresolved (page capture 2005-07-01 is after it). Edison, Tengu:
  unresolved (a ruling supports the script; its range is not shown).
- **Action.** Not shipped: `supported` is required at both snapshots.

### 6.12 Second Coin Toss (600000017)

- **Difference.** Each copy redoes a toss; the modern card is limited by name.
- **Sources.** UDE page 2005-07-01, Konami-hosted FAQ 2008-12-15: "Even if multiple
  "Second Coin Toss" cards are active, you can only redo each coin toss once." Also: it
  "only applies when you perform a coin toss, not when your opponent performs a coin
  toss"; "If an effect requires multiple coin flips, like "Barrel Dragon", you would redo
  all 3 coin flips."
- **Verdicts.** GOAT, Edison, Tengu: unresolved: the ruling contradicts the per-copy
  difference; its range is not shown.
- **Action.** Not shipped. The owner is asked.

## 7. How many other errata records rest on printed text alone

Counted without adjudicating (`data/errata/*.json`, 296 records, at `main`):

- Records with at least one transition of kind `functional`: 120 (104 excluding the
  sixteen cards of this round).
- Of the 104: **none** carries a ruling-type source on its functional transition (a source
  id starting `ude-` or `konami-`, or containing `ruling` or `faq`). The functional
  transitions cite `yugipedia-card-errata`, `yugipedia-set-pages`, `ignis-cardscripts`,
  `ignis-babelcdb`, `ignis-lflists`, and in 22 cases `edisonformat-functional-errata`, a
  community list, not a ruling.
- **80** of the 104 also never mention a ruling, FAQ, Netrep answer or judge list in their
  functional summaries or review notes.

A functional call from printed text is often right, for example a changed effect or a new
cost. The count says only how many rest on printed text alone. Method: a script over the
records' `sources`, `summary` and `review.notes` fields; it does not read the sources
themselves.

## 8. Leads, resolved

| lead | result |
|---|---|
| Zorc, UDE Netrep 2007-10-11 | **Confirmed** at the archived thread (capture 2007-10-27): "You can only roll the 6-sided die once." The FAQ entries say nothing of a limit. The Japanese "１ターンに１度" since the first printing is confirmed only at Yugipedia's transcription; the printing was not opened. |
| Second Coin Toss, "own tosses only; each toss redone once" | **Confirmed** at the card FAQ (2005-07-01, 2008-12-15, 2009-02-26); Yugipedia lists it with no citation. |
| Goddess of Whim, "once per turn" | **Confirmed** at the Konami-hosted FAQ (2008-12-15) and the UDE-hosted copy (2009-02-26). Not on the 2005-07-01 page. |
| Rise of the Snake Deity, thread 830322 | **Confirmed**, with a correction: the answer is the Netrep post of 2007-08-17 in a thread whose Yugipedia-cited post (2007-08-31) is a later remark. The 2007-11-01 capture holds both. |
| Green Baboon, face-up | **Confirmed** (Netrep 2007-09-28; FAQ). **Also found:** the FAQ allows the Damage Step, and Konami's lists from 2009-07-30 do not. |
| Dice Re-Roll, per activation | **Confirmed** at the FAQ (2005-07-01, 2008-12-15). It agrees with the script. |
| Gigantes, Heraklinos, Metalzoa, Malefic Blue-Eyes, OCG revival | **Confirmed** at the Konami OCG database, four pages, retrieved 2026-09-29; current and undated. OCG only. A TCG source adopts the class rule (section 3), not these four pages. |
| Project Ignis's GOAT list keeps the modern implementation of all eight round-034 cards | **Partly confirmed:** the GOAT list carries the modern code of six (Gigantes, The Rock Spirit, Garuda the Wind Spirit, Dark Master - Zorc, Dice Re-Roll, Second Coin Toss); VW-Tiger Catapult and Gladiator Beast Heraklinos are not in it. A curator's choice about a 2005 list, not a ruling about 2010-2011. |

## 9. What this research does not establish

- Whether any UDE card ruling stood at 2010-04-24 or 2011-09-17 (section 5).
- Anything about the GOAT period for the class (section 3).
- That Konami's 2009-12-07 article is unaltered since 2009: its earliest capture is 2015.
- The Damage Step position of Konami-era per-card exceptions other than those read. A
  card with a ruling of its own could differ from the rulebook rule; none was found for
  Rise of the Snake Deity, Soul Rope or Green Baboon beyond the Konami list quoted.
- Konami's per-set ruling PDFs for Machina Mayhem, Starlight Road/Hidden Arsenal/Warriors'
  Strike/Starter Deck 2009, The Shining Darkness, Duelist Revolution, Absolute Powerforce,
  Stardust Overdrive, Ancient Prophecy, Raging Battle and Crimson Crisis were not
  retrievable in this session (Internet Archive timeouts). Those read (Extreme Victory,
  Hidden Arsenal 3, Storm of Ragnarok, Gold Series 3 / Tag Force 5, Starstrike Blast) contain none of the sixteen cards.

Owner's questions from this research are stated in plain terms in the round report.
